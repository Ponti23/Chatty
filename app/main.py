from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.embeddings import EmbeddingService
from app.vector_store import VectorStoreClient
from app.storage import StorageClient
from app.routers import ingest
from app.routers import auth as auth_router
from app.routers import chat as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield


app = FastAPI(title="Knowledge Base Ingestion Service", lifespan=lifespan)
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(chat_router.router, prefix="/api/v1")
