import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.vector_store import VectorStoreClient
from app.embeddings import EmbeddingService
from app.storage import StorageClient
from app.config import settings

TEST_DATABASE_URL = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"


@pytest.fixture(autouse=True, scope="session")
def init_app_state():
    app.state.embeddings = EmbeddingService(
        settings.embedding_model, batch_size=settings.embedding_batch_size
    )
    app.state.vector_store = VectorStoreClient(settings.qdrant_host, settings.qdrant_port)
    app.state.vector_store.ensure_collection()
    app.state.storage = StorageClient(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
        settings.minio_bucket,
    )
    app.state.storage.ensure_bucket()


@pytest.fixture(autouse=True)
def override_app_db():
    from app.database import get_db

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def real_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(real_client: AsyncClient):
    """Register a fresh user and return JWT auth headers for the integration tests."""
    unique = uuid.uuid4().hex[:8]
    email = f"inttest_{unique}@example.com"
    password = "TestPass123!"
    tenant_name = f"Integration Tenant {unique}"

    resp = await real_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "tenant_name": tenant_name},
    )
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def vector_store():
    client = VectorStoreClient(settings.qdrant_host, settings.qdrant_port)
    client.ensure_collection()
    return client
