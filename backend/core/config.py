"""
Centralized configuration management using Pydantic Settings.
All configuration is strongly typed and validated.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with strong typing and validation."""
    
    # ========== Application Settings ==========
    PROJECT_NAME: str = "Bidding Intelligence System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DEBUG: bool = False
    
    # ========== Server Settings ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    RELOAD: bool = False
    
    # ========== Database Settings ==========
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "bidding_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def sync_database_url(self) -> str:
        """Construct sync database URL (for migrations)."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # ========== Redis Settings ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========== Celery Settings ==========
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL (defaults to Redis)."""
        return self.CELERY_BROKER_URL or self.redis_url
    
    @property
    def celery_backend(self) -> str:
        """Get Celery result backend URL (defaults to Redis)."""
        return self.CELERY_RESULT_BACKEND or self.redis_url
    
    # ========== AI Model Settings ==========
    OPENAI_API_KEY: Optional[str] = None  # 测试环境下可选
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.3
    
    # Optional: Multi-model support
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # ========== File Upload Settings ==========
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".doc"]
    
    # ========== Cache Settings ==========
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 3600  # 1 hour
    CACHE_PARSED_FILE_TTL: int = 3600  # 1 hour
    CACHE_CHAPTER_LOGIC_TTL: int = 86400  # 24 hours
    CACHE_GLOBAL_LOGIC_TTL: int = 86400  # 24 hours
    
    # ========== Security Settings ==========
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ========== CORS Settings ==========
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # ========== Logging Settings ==========
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_ROTATION: str = "00:00"  # Midnight
    LOG_RETENTION: str = "10 days"
    LOG_FORMAT: str = "json"  # json or text
    
    # ========== OCR Settings ==========
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "ch"  # Chinese + English
    OCR_USE_GPU: bool = False
    
    # ========== Performance Settings ==========
    MAX_CONCURRENT_TASKS: int = 10
    PARSING_TIMEOUT: int = 300  # 5 minutes
    GENERATION_TIMEOUT: int = 600  # 10 minutes
    
    # ========== Feature Flags ==========
    ENABLE_HYBRID_SEARCH: bool = True
    ENABLE_STRUCTURED_OUTPUT: bool = True
    ENABLE_MULTI_MODEL: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to ensure settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
