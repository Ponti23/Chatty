import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Tenant


class TenantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, slug: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug)
        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def list_all(self) -> list[Tenant]:
        result = await self.session.execute(select(Tenant))
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        result = await self.session.execute(
            select(Tenant).where(Tenant.tenant_id == uuid.UUID(tenant_id))
        )
        return result.scalar_one_or_none()
