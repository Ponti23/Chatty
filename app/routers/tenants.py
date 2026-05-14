from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import require_admin
from app.repositories.tenants import TenantRepository

router = APIRouter()


class TenantCreate(BaseModel):
    name: str
    slug: str


@router.get("/tenants")
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = TenantRepository(db)
    tenants = await repo.list_all()
    return [
        {"tenant_id": str(t.tenant_id), "name": t.name, "slug": t.slug}
        for t in tenants
    ]


@router.post("/tenants", status_code=201)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = TenantRepository(db)
    tenant = await repo.create(body.name, body.slug)
    return {"tenant_id": str(tenant.tenant_id), "name": tenant.name, "slug": tenant.slug}
