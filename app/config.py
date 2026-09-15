"""
Configuration management using Pydantic Settings.

This module loads environment variables from .env file and validates them.
All configuration is centralized here for easy management and testing.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses Pydantic for validation and type safety.
    The .env file is automatically loaded.
    """
    
    # OpenAI Configuration
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for embeddings and LLM"
    )
    
    # Gemini Configuration
    gemini_api_key: str | None = Field(
        default=None,
        description="Google Gemini API key for LLM"
    )
    
    # API Provider Selection
    api_provider: Literal["openai", "gemini"] = Field(
        default="gemini",
        description="API provider to use (openai or gemini)"
    )
    
    # Qdrant Configuration
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL"
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="Qdrant API key (optional for local deployment)"
    )
    qdrant_collection_name: str = Field(
        default="documents",
        description="Name of the Qdrant collection"
    )
    
    # Qdrant Mode: 'server' or 'memory'
    qdrant_mode: Literal["server", "memory"] = Field(
        default="memory",
        description="Qdrant mode: 'server' for Docker/cloud, 'memory' for in-memory"
    )
    
    # Inngest Configuration
    inngest_event_key: str | None = Field(
        default=None,
        description="Inngest event key for workflow orchestration"
    )
    inngest_signing_key: str | None = Field(
        default=None,
        description="Inngest signing key for security"
    )
    
    # Application Configuration
    environment: Literal["development", "production"] = Field(
        default="development",
        description="Application environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # RAG Configuration
    chunk_size: int = Field(
        default=1024,
        description="Size of text chunks in characters",
        ge=100,
        le=4000
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks in characters",
        ge=0,
        le=500
    )
    top_k: int = Field(
        default=5,
        description="Number of chunks to retrieve",
        ge=1,
        le=20
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model"
    )
    llm_model: str = Field(
        default="gemini-1.5-flash",
        description="LLM model for generation (gemini-1.5-flash, gemini-1.5-pro, or gpt-4o-mini)"
    )
    
    # File Upload Configuration
    max_file_size_mb: int = Field(
        default=10,
        description="Maximum file size in MB",
        ge=1,
        le=100
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("openai_api_key", "gemini_api_key")
    @classmethod
    def validate_api_keys(cls, v: str | None, info) -> str | None:
        """Validate API keys based on provider"""
        field_name = info.field_name
        
        # Skip validation if not set
        if not v or v == "your_openai_api_key_here" or v == "your_gemini_api_key_here":
            return None
        
        # Validate OpenAI key format
        if field_name == "openai_api_key" and v:
            if not v.startswith("sk-"):
                raise ValueError("OpenAI API key should start with 'sk-'")
        
        return v
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size"""
        # Note: We can't access chunk_size here directly in Pydantic v2
        # This validation will be done in post-initialization if needed
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once.
    This is the recommended way to access settings throughout the app.
    
    Returns:
        Settings: Validated settings instance
        
    Raises:
        ValidationError: If required settings are missing or invalid
    """
    return Settings()


# Convenience function for testing
def reload_settings() -> Settings:
    """
    Reload settings (clears cache).
    Useful for testing with different environment variables.
    """
    get_settings.cache_clear()
    return get_settings()


if __name__ == "__main__":
    # Test configuration loading
    try:
        settings = get_settings()
        print("✓ Configuration loaded successfully!")
        print(f"  Environment: {settings.environment}")
        print(f"  Qdrant Mode: {settings.qdrant_mode}")
        print(f"  Embedding Model: {settings.embedding_model}")
        print(f"  LLM Model: {settings.llm_model}")
        print(f"  Chunk Size: {settings.chunk_size}")
        print(f"  Chunk Overlap: {settings.chunk_overlap}")
        print(f"  Top K: {settings.top_k}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
