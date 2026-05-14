from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "raw-sources"
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_batch_size: int = 32
    chunk_size: int = 512
    chunk_overlap: int = 64
    max_file_size_mb: int = 50
    default_chunk_quota: int = 10000
    request_timeout_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
