from pydantic import BaseModel
from sqlalchemy.orm import Session

import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

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
    lower_text = user_text.lower()
    if "what can you do" in lower_text or "what do you do" in lower_text or "who are you" in lower_text:
        reply_text = (
            "I am an AI assistant designed to help you discover and apply for government welfare schemes. "
            "I can check your eligibility based on your profile, explain scheme details, and guide you through the application process."
        )
        db_user_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="user", content=user_text)
        db.add(db_user_msg)
        db.commit()
        db_asst_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="assistant", content=reply_text)
        db.add(db_asst_msg)
        db.commit()
        return ChatOut(reply=reply_text)

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


@router.post("/message_stream")
def chat_message_stream(body: ChatIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Stream a text-only chat reply with full conversation history."""
    from chat.rag import chat_reply_stream

    user_text = ""
    for m in reversed(body.messages):
        if str(m.role).strip().lower() == "user" and str(m.content).strip():
            user_text = str(m.content).strip()
            break
    if not user_text:
        async def empty_generator():
            yield f"data: {json.dumps({'type': 'token', 'token': 'Please share your query so I can help you find relevant schemes.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(empty_generator(), media_type="text/event-stream")

    lower_text = user_text.lower()
    if "what can you do" in lower_text or "what do you do" in lower_text or "who are you" in lower_text:
        reply_text = (
            "I am an AI assistant designed to help you discover and apply for government welfare schemes. "
            "I can check your eligibility based on your profile, explain scheme details, and guide you through the application process."
        )

        async def canned_generator():
            yield f"data: {json.dumps({'type': 'token', 'token': reply_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        db_user_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="user", content=user_text)
        db.add(db_user_msg)
        db.commit()
        db_asst_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="assistant", content=reply_text)
        db.add(db_asst_msg)
        db.commit()
        return StreamingResponse(canned_generator(), media_type="text/event-stream")

    db_user_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="user", content=user_text)
    db.add(db_user_msg)
    db.commit()

    db_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id, ChatMessage.session_id == body.session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in db_msgs]

    async def event_generator():
        full_reply = ""
        for chunk in chat_reply_stream(history):
            if await request.is_disconnected():
                return
            if not chunk:
                continue
            full_reply += chunk
            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"

        db_asst_msg = ChatMessage(user_id=user.id, session_id=body.session_id, role="assistant", content=full_reply)
        db.add(db_asst_msg)
        db.commit()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
