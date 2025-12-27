"""Configuration management for AI Prompt Studio."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    
    # Vector Store Configuration
    vector_store_path: str = Field(default="./data/vector_store", env="VECTOR_STORE_PATH")
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    
    # RLAIF Configuration
    min_optimization_iterations: int = Field(default=3, env="MIN_OPTIMIZATION_ITERATIONS")
    max_optimization_iterations: int = Field(default=5, env="MAX_OPTIMIZATION_ITERATIONS")
    
    # File Upload Configuration
    upload_dir: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the settings instance."""
    return settings
