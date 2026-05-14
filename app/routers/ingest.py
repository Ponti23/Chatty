import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.chunking import Chunker
from app.parsers import PARSERS, detect_type
from app.repositories.sources import SourceRepository
from app.config import settings

router = APIRouter()


@router.post("/sources", status_code=201)
async def ingest_source(
    request: Request,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    x_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    embeddings = request.app.state.embeddings
    vector_store = request.app.state.vector_store
    storage = request.app.state.storage
    repo = SourceRepository(db)

    if file is not None:
        content = await file.read()
        filename = file.filename or "upload"
        source_type = detect_type(filename)
    elif url is not None:
        content = url.encode()
        filename = url
        source_type = "url"
    else:
        raise HTTPException(status_code=400, detail="Either file or url must be provided")

    if source_type not in PARSERS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {filename}")

    if file is not None and len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size")

    source_id = str(uuid.uuid4())
    storage.save(x_tenant_id, source_id, filename, content)
    source = await repo.create(x_tenant_id, source_id, filename, source_type)

    try:
        if source_type == "url":
            segments = PARSERS["url"](url)
        else:
            segments = PARSERS[source_type](content)

        chunker = Chunker(source_id=source_id, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
        chunks = chunker.chunk(segments)

        existing_count = await repo.get_chunk_count(x_tenant_id)
        if existing_count + len(chunks) > settings.default_chunk_quota:
            raise HTTPException(status_code=429, detail="Tenant chunk quota exceeded")

        vector_store.delete_by_source(x_tenant_id, source_id)

        texts = [c.text for c in chunks]
        vectors = embeddings.embed_batch(texts)

        vector_store.upsert_chunks(x_tenant_id, chunks, vectors)
        await repo.update_status(source_id, "indexed", chunk_count=len(chunks))

        return {"source_id": source_id, "chunk_count": len(chunks), "status": "indexed"}

    except HTTPException:
        raise
    except Exception as exc:
        await repo.update_status(source_id, "failed", error_message=str(exc))
        raise HTTPException(status_code=422, detail=str(exc))
