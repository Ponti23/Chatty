import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token
from app.repositories.users import UserRepository
from app.repositories.tenants import TenantRepository

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    tenant_name: str


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/auth/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    tenant_repo = TenantRepository(db)

    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    slug = _slugify(body.tenant_name)
    tenant = await tenant_repo.create(body.tenant_name, slug)
    user = await user_repo.create(
        email=body.email,
        hashed_password=hash_password(body.password),
        tenant_id=str(tenant.tenant_id),
        role="admin",
    )
    token = create_access_token(str(user.user_id), str(user.tenant_id), user.role)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user.user_id), str(user.tenant_id), user.role)
    return {"access_token": token, "token_type": "bearer"}
