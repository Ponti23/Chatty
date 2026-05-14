import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user
from app.repositories.conversations import ConversationRepository
from app.repositories.messages import MessageRepository
from app import rag
from app.config import settings

router = APIRouter()


class ConversationCreate(BaseModel):
    title: str = "New conversation"


class MessageSend(BaseModel):
    content: str


@router.post("/conversations", status_code=201)
async def create_conversation(
    body: ConversationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.create(
        tenant_id=current_user["tenant_id"],
        user_id=current_user["sub"],
        title=body.title,
    )
    return {
        "conversation_id": str(conv.conversation_id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
    }


@router.get("/conversations")
async def list_conversations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    convs = await repo.list_by_user(current_user["sub"])
    return [
        {"conversation_id": str(c.conversation_id), "title": c.title, "created_at": c.created_at.isoformat()}
        for c in convs
    ]


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id)
    if not conv or str(conv.user_id) != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await repo.delete(conversation_id)


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv_repo = ConversationRepository(db)
    conv = await conv_repo.get_by_id(conversation_id)
    if not conv or str(conv.user_id) != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_repo = MessageRepository(db)
    messages = await msg_repo.list_by_conversation(conversation_id)
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: MessageSend,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv_repo = ConversationRepository(db)
    conv = await conv_repo.get_by_id(conversation_id)
    if not conv or str(conv.user_id) != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_repo = MessageRepository(db)
    await msg_repo.create(conversation_id, "user", body.content)

    history_msgs = await msg_repo.list_by_conversation(conversation_id, limit=20)
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

    embeddings = request.app.state.embeddings
    vector_store = request.app.state.vector_store
    tenant_id = current_user["tenant_id"]

    accumulated: list[str] = []

    async def generate():
        async for token in rag.stream_answer(
            tenant_id=tenant_id,
            query=body.content,
            history=history,
            embeddings=embeddings,
            vector_store=vector_store,
            ollama_base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        ):
            accumulated.append(token)
            yield f"data: {token}\n\n"

        full_response = "".join(accumulated)
        await msg_repo.create(conversation_id, "assistant", full_response)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
