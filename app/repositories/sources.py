import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Source


class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant_id: str, source_id: str, filename: str, source_type: str) -> Source:
        source = Source(
            source_id=uuid.UUID(source_id),
            tenant_id=uuid.UUID(tenant_id),
            filename=filename,
            source_type=source_type,
            status="indexing",
        )
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def update_status(
        self,
        source_id: str,
        status: str,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> Source:
        stmt = update(Source).where(Source.source_id == uuid.UUID(source_id)).values(
            status=status, chunk_count=chunk_count, error_message=error_message
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.session.get(Source, uuid.UUID(source_id))

    async def get_by_tenant(self, tenant_id: str) -> list[Source]:
        result = await self.session.execute(
            select(Source).where(Source.tenant_id == uuid.UUID(tenant_id))
        )
        return list(result.scalars().all())

    async def get_chunk_count(self, tenant_id: str) -> int:
        sources = await self.get_by_tenant(tenant_id)
        return sum(s.chunk_count or 0 for s in sources if s.status == "indexed")

    async def delete(self, source_id: str) -> None:
        source = await self.session.get(Source, uuid.UUID(source_id))
        if source:
            await self.session.delete(source)
            await self.session.commit()
