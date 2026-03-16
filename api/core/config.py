from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import field_validator

def clean_env_value(value: str) -> str:
    """Remove surrounding quotes from environment variable values."""
    if not value:
        return value
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value

# Load .env file for local development (doesn't override existing env vars)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Debug logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Raw OPENAI_API_KEY from environment: {repr(os.getenv('OPENAI_API_KEY'))}")

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
    
    @field_validator('OPENAI_API_KEY', 'CORE_API_KEY', 'WEAVIATE_URL', 'WEAVIATE_API_KEY', 'OPIK_API_KEY', 'OPIK_URL', mode='before')
    @classmethod
    def clean_api_keys(cls, v):
        if isinstance(v, str):
            cleaned = clean_env_value(v)
            logger.info(f"Cleaning env value: {repr(v)} -> {repr(cleaned)}")
            return cleaned
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()

