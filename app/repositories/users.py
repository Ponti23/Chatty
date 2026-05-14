import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, hashed_password: str, tenant_id: str, role: str = "user") -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            tenant_id=uuid.UUID(tenant_id),
            role=role,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.user_id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()
