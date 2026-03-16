from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly to override system environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Researcher API"
    DEBUG: bool = True
    
    # CoreApi
    CORE_API_KEY: Optional[str] = None

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Opik (Comet) tracing / evals
    # Docs: https://www.comet.com/docs/opik/
    OPIK_API_KEY: Optional[str] = None
    OPIK_URL: Optional[str] = None  # Optional: self-hosted instance URL
    OPIK_PROJECT: str = "ai_researcher"
    OPIK_ENABLED: bool = True

    # Deployment: optionally serve the built frontend from the backend container
    SERVE_CLIENT: bool = False
   
    # Weaviate
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None
    WEAVIATE_CLUSTER: Optional[str] = None

    # Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"  # Change this in production!
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 7  # 7 days
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()

