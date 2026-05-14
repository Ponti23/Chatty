import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings
from app.embeddings import EmbeddingService
from app.vector_store import VectorStoreClient
from app.storage import StorageClient
from app.routers import ingest
from app.routers import auth as auth_router
from app.routers import tenants as tenants_router
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
    if settings.jwt_secret_key == "changeme-in-production":
        logging.warning("JWT_SECRET_KEY is using the insecure default. Set a strong secret in .env before production use.")
    yield


app = FastAPI(title="Chatbot Platform API", lifespan=lifespan)
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(tenants_router.router, prefix="/api/v1")
app.include_router(chat_router.router, prefix="/api/v1")

# Serve frontend static files if built dist exists
_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
