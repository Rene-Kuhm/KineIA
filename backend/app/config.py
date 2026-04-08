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

    # LLM
    anthropic_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"
    llm_provider: str = "groq"  # anthropic, google, groq, ollama

    # Auth
    jwt_secret: str = "changeme_jwt_secret_at_least_32_chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 50
    retriever_top_k: int = 10
    reranker_top_k: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
