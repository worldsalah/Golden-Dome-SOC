from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Golden Dome SOC API"
    APP_VERSION: str = "0.3.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1"
    SEED_DEMO_DATA: bool = False
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@goldendome.local"
    ADMIN_PASSWORD: str = "admin"
    ALLOW_BOOTSTRAP_REGISTRATION: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/goldendome"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Wazuh API
    WAZUH_API_URL: str = "https://localhost:55000"
    WAZUH_API_USERNAME: str = "wazuh"
    WAZUH_API_PASSWORD: str = "wazuh"
    WAZUH_API_VERIFY_SSL: bool = False
    WAZUH_API_TIMEOUT: int = 30

    # OpenSearch / Wazuh Indexer
    OPENSEARCH_URL: str = "https://localhost:9200"
    OPENSEARCH_USERNAME: str = "admin"
    OPENSEARCH_PASSWORD: str = "admin"
    OPENSEARCH_VERIFY_SSL: bool = False

    # AI / Local LLM (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_TIMEOUT: int = 45
    AI_FALLBACK_ENABLED: bool = True

    # SMTP / Notifications
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_FROM: str = "soc@goldendome.local"
    SOAR_AUTO_TRIGGER_ENABLED: bool = True

    # Threat Intelligence APIs (free tiers / community keys)
    ABUSEIPDB_API_KEY: str = ""
    VIRUSTOTAL_API_KEY: str = ""
    ALIENVAULT_OTX_API_KEY: str = ""
    URLHAUS_API_URL: str = "https://urlhaus-api.abuse.ch/v1"
    CISA_KEV_URL: str = "https://api.cisa.gov/known-exploited-vulnerabilities/catalog"
    TI_CACHE_HOURS: int = 24

    # Risk scoring weights (must sum to 1.0)
    RISK_WEIGHT_SEVERITY: float = 0.30
    RISK_WEIGHT_CRITICALITY: float = 0.20
    RISK_WEIGHT_VULNERABILITY: float = 0.20
    RISK_WEIGHT_THREAT_INTEL: float = 0.15
    RISK_WEIGHT_HISTORICAL: float = 0.15

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> List[str]:
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
