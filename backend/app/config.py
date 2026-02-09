"""Application configuration management."""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str
    openai_api_key: str

    # Database
    database_url: str

    # ChromaDB
    chromadb_path: str = "/app/data/chromadb"

    # Application
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # LLM Configuration
    default_llm_provider: str = "anthropic"  # anthropic or openai
    claude_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4-turbo-preview"
    claude_eval_model: str = "claude-opus-4-20250514"  # For LLM-as-judge
    temperature: float = 0.7
    max_tokens: int = 1024

    # Retrieval Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    top_k: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Data paths
    raw_data_path: str = "/app/data/raw"
    processed_data_path: str = "/app/data/processed"
    golden_sets_path: str = "/app/data/golden_sets"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
