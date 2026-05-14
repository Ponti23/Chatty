import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Message


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(
            conversation_id=uuid.UUID(conversation_id),
            role=role,
            content=content
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def list_by_conversation(self, conversation_id: str, limit: int = 50) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == uuid.UUID(conversation_id))
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
