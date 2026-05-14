import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"


@pytest.fixture(autouse=True)
def override_app_db():
    from app.main import app
    from app.database import get_db

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)
