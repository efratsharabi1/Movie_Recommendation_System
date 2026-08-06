from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.query_handlers.chat_query_handler import ChatQueryHandler

router = APIRouter(prefix="/api", tags=["AI Chat"])

class ChatRequest(BaseModel):
    prompt: str
    user_id: str

@router.post("/ai/chat")
async def chat_with_ai(request: ChatRequest):
    # The Controller simply creates an instance of the Handler and calls it
    handler = ChatQueryHandler()
    result = await handler.handle_chat(request.prompt, request.user_id)
    return result