from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from auth.db import SessionLocal
from auth.deps import get_current_user
from auth.models import User, ChatMessage
from eligibility.profile_extract import infer_profile_from_query
from eligibility.service import run_eligibility_pipeline

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
    messages: list[Msg]


class ChatOut(BaseModel):
    reply: str


@router.get("/history", response_model=list[Msg])
def get_chat_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.id.asc()).all()
    return [{"role": m.role, "content": m.content} for m in db_msgs]


@router.delete("/history")
def clear_chat_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()
    return {"ok": True}


@router.post("/message", response_model=ChatOut)
def chat_message(body: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = [m.model_dump() for m in body.messages]
    user_text = ""

    for m in reversed(msgs):
        if str(m.get("role", "")).strip().lower() == "user" and str(m.get("content", "")).strip():
            user_text = str(m.get("content")).strip()
            break

    if not user_text:
        return ChatOut(reply="Please share your query so I can check your eligibility.")

    db_user_msg = ChatMessage(user_id=user.id, role="user", content=user_text)
    db.add(db_user_msg)
    db.commit()

    profile = infer_profile_from_query(user_text)
    pipeline = run_eligibility_pipeline(raw_text=user_text, profile=profile, confidence=0.9)
    text = pipeline.response_text

    db_asst_msg = ChatMessage(user_id=user.id, role="assistant", content=text)
    db.add(db_asst_msg)
    db.commit()

    return ChatOut(reply=text)
