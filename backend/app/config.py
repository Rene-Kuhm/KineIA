from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql://kineia:changeme@postgres:5432/kineia"

    # Qdrant
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "kineia_knowledge"
    qdrant_hybrid_collection: str = "kineia_knowledge_v2"
    qdrant_dense_vector_name: str = "dense"
    qdrant_sparse_vector_name: str = "sparse"
    qdrant_write_mode: Literal["legacy", "dual"] = "legacy"

    # LLM
    anthropic_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""
    deepseek_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"
    llm_provider: str = "deepseek"  # anthropic, google, groq, deepseek, ollama

    # Auth
    jwt_secret: str = "changeme_jwt_secret_at_least_32_chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # RAG
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024  # 384 for all-MiniLM-L6-v2 fallback
    chunk_size: int = 512
    chunk_overlap: int = 50
    retriever_top_k: int = 10
    reranker_top_k: int = 5
    retriever_hybrid_shadow_enabled: bool = False
    retriever_hybrid_candidate_k: int = Field(default=30, ge=1, le=100)
    retriever_hybrid_timeout_seconds: int = Field(default=2, ge=1, le=10)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
