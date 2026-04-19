from pydantic import BaseModel

from fastapi import APIRouter, Depends

from auth.deps import get_current_user
from auth.models import User
from chat.rag import chat_reply

router = APIRouter(prefix="/chat", tags=["chat"])


class Msg(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    messages: list[Msg]


class ChatOut(BaseModel):
    reply: str


@router.post("/message", response_model=ChatOut)
def chat_message(body: ChatIn, user: User = Depends(get_current_user)):
    msgs = [m.model_dump() for m in body.messages]
    text = chat_reply(msgs)
    return ChatOut(reply=text)
