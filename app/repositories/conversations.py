import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant_id: str, user_id: str, title: str = "New conversation") -> Conversation:
        conv = Conversation(
            tenant_id=uuid.UUID(tenant_id),
            user_id=uuid.UUID(user_id),
            title=title
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def list_by_user(self, user_id: str) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation).where(Conversation.user_id == uuid.UUID(user_id)).order_by(Conversation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.conversation_id == uuid.UUID(conversation_id))
        )
        return result.scalar_one_or_none()

    async def delete(self, conversation_id: str) -> None:
        conv = await self.get_by_id(conversation_id)
        if conv:
            await self.session.delete(conv)
            await self.session.commit()
