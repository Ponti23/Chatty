from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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
    jwt_secret_key: str = "changeme-in-production"
    access_token_expire_minutes: int = 60
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"


settings = Settings()
