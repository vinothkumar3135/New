"""Centralized configuration management for Infoez backend."""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file from backend root
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

class Settings(BaseModel):
    APP_NAME: str = "Infoez API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")

    # Database
    MONGO_URL: str = Field(default_factory=lambda: os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    DB_NAME: str = Field(default_factory=lambda: os.getenv("DB_NAME", "localconnect-justdial"))

    # Auth & JWT
    JWT_SECRET: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET", "infoez-super-secret-key-change-in-production")
    )
    JWT_ALGORITHM: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_DAYS: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "30"))
    )

    # CORS
    CORS_ORIGINS: str = Field(default_factory=lambda: os.getenv("CORS_ORIGINS", ""))

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Emergent Universal Object Storage (Integrations)
    INTEGRATION_PROXY_URL: str = Field(
        default_factory=lambda: (
            os.getenv("INTEGRATION_PROXY_URL") or "https://integrations.emergentagent.com"
        ).strip().rstrip("/")
    )
    EMERGENT_LLM_KEY: str = Field(default_factory=lambda: os.getenv("EMERGENT_LLM_KEY", ""))

    @property
    def storage_url(self) -> str:
        return f"{self.INTEGRATION_PROXY_URL}/objstore/api/v1/storage"

settings = Settings()
