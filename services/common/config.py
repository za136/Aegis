"""Global Application Configuration using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform-wide settings loaded from environment or .env file."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Gemini AI Model Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # Database (PostgreSQL 16 with pgvector)
    POSTGRES_USER: str = "aegis"
    POSTGRES_PASSWORD: str = "aegis_secure_password"
    POSTGRES_DB: str = "aegis_meridian"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://aegis:aegis_secure_password@localhost:5432/aegis_meridian"

    # Redis Cache & Ephemeral State
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Event Bus (Redpanda - Kafka API Compatible)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SCHEMA_REGISTRY_URL: str = "http://localhost:8081"

    # Identity & JWT Configuration
    JWT_SECRET_KEY: str = "development_secret_key_change_in_production_32b"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Keycloak (Optional OIDC Container)
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "meridian"
    KEYCLOAK_CLIENT_ID: str = "meridian-portal"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None

    # Autonomy Limits
    TOOL_GATEWAY_DEFAULT_AUTONOMY: str = "A1"
    MAX_AUTONOMOUS_TRANSFER_LIMIT_USD: float = 100.00
    REPAIR_AUTO_THRESHOLD_USD: float = 250.00


settings = Settings()
