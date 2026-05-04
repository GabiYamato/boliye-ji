from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from auth.db import SessionLocal
from auth.deps import get_current_user
from auth.models import User, ChatMessage
from chat.rag import chat_reply

router = APIRouter(prefix="/chat", tags=["chat"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Msg(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    session_id: str = "default"
    messages: list[Msg]


class ChatOut(BaseModel):
    reply: str


@router.get("/sessions")
def get_chat_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Group by session_id and get the first user message as preview
    from sqlalchemy import func
    subq = db.query(
        ChatMessage.session_id,
        func.min(ChatMessage.id).label('min_id')
    ).filter(
        ChatMessage.user_id == user.id,
        ChatMessage.role == 'user'
    ).group_by(ChatMessage.session_id).subquery()
    
    sessions_msgs = db.query(ChatMessage).join(
        subq, 
        (ChatMessage.session_id == subq.c.session_id) & (ChatMessage.id == subq.c.min_id)
    ).order_by(ChatMessage.id.desc()).all()
    
    return [{"id": m.session_id, "preview": m.content[:40] + ("..." if len(m.content) > 40 else "")} for m in sessions_msgs]


@router.get("/history", response_model=list[Msg])
def get_chat_history(session_id: str = "default", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_msgs = db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id,
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.id.asc()).all()
    return [{"role": m.role, "content": m.content} for m in db_msgs]


@router.delete("/history")
def clear_chat_history(session_id: str = "default", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id,
        ChatMessage.session_id == session_id
    ).delete()
    db.commit()
    return {"ok": True}


@router.post("/message", response_model=ChatOut)
def chat_message(body: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Handle a text chat message with full conversation history.

    The key change: we load ALL past messages from the DB and send them
    to the LLM, so it never forgets what the user already told it.
    """
    # Extract the new user message
    user_text = ""
    for m in reversed(body.messages):
        if str(m.role).strip().lower() == "user" and str(m.content).strip():
            user_text = str(m.content).strip()
            break

    if not user_text:
        return ChatOut(reply="Please share your query so I can help you find relevant schemes.")

    # Store user message
    db_user_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="user", content=user_text)
    db.add(db_user_msg)
    db.commit()

    # Load FULL conversation history from DB for context
    db_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id, ChatMessage.session_id == body.session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in db_msgs]

    # Generate reply with full history
    reply_text = chat_reply(history)

    # Store assistant reply
    db_asst_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="assistant", content=reply_text)
    db.add(db_asst_msg)
    db.commit()

    return ChatOut(reply=reply_text)
