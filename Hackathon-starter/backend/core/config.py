"""Application Configuration - Loads settings from environment variables"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Info
    APP_NAME: str = "Zava AI Portal"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/zava"

    # Azure OpenAI Configuration (legacy)
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"

    # NVIDIA NIM on Azure AI Foundry
    NVIDIA_NIM_ENDPOINT: Optional[str] = None
    NVIDIA_NIM_API_KEY: Optional[str] = None
    NVIDIA_NIM_MODEL: str = "nemotron-nano-zava"

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5000,http://localhost:8000"

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()