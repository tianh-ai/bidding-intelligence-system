"""
Centralized configuration management using Pydantic Settings.
All configuration is strongly typed and validated.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with strong typing and validation."""
    
    # ========== Application Settings ==========
    PROJECT_NAME: str = "Bidding Intelligence System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DEBUG: bool = False
    
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
        """Construct async database URL.
        
        Supports both Docker (postgres:5432) and local (localhost:5433) environments.
        Use DB_HOST and DB_PORT environment variables to configure.
        """
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
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = "sk-1fc432ea945d4c448f3699d674808167"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Ollama Configuration (本地 LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "mxbai-embed-large"  # 高精度 embedding 模型 (1024维)
    OLLAMA_CHAT_MODEL: str = "qwen2.5:latest"  # 可选的聊天模型
    USE_OLLAMA_FOR_EMBEDDINGS: bool = True  # 默认使用 Ollama 生成 embeddings
    
    # Qwen Configuration
    QWEN_API_KEY: str = "sk-17745e25a6b74f4994de3b8b42341b57"
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"
    
    # ========== File Upload Settings ==========
    UPLOAD_DIR: str = "/app/data/uploads"  # Docker 挂载到 SSD
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"]

    # 图片存储目录（本地/容器均可覆盖）
    IMAGE_STORAGE_DIR: str = "/app/data/images"
    
    @property
    def upload_path(self) -> str:
        """获取上传目录的绝对路径，自动创建目录"""
        import os
        # 如果是相对路径，相对于项目根目录
        if not os.path.isabs(self.UPLOAD_DIR):
            # 获取项目根目录（backend目录的父目录）
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_path = os.path.join(base_dir, self.UPLOAD_DIR)
        else:
            upload_path = self.UPLOAD_DIR
        
        # 自动创建目录
        os.makedirs(upload_path, exist_ok=True)
        return upload_path

    @property
    def image_storage_path(self) -> str:
        """获取图片存储目录，优先使用配置路径，不可写时回退到本地 data/images。"""
        import os

        def ensure_dir(path: str) -> str:
            p = Path(path)
            p.mkdir(parents=True, exist_ok=True)
            return str(p)

        # 绝对路径：直接尝试创建，失败则回退
        if os.path.isabs(self.IMAGE_STORAGE_DIR):
            try:
                return ensure_dir(self.IMAGE_STORAGE_DIR)
            except OSError:
                pass  # 只在只读文件系统时回退
        # 相对路径或回退路径：使用项目根目录下 data/images
        base_dir = Path(__file__).resolve().parent.parent  # backend 目录
        fallback = base_dir.parent / "data" / "images"
        return ensure_dir(fallback)
    
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
    PORT: int = 8000  # API server port (must match .env PORT and frontend proxy)
    HOST: str = "0.0.0.0"  # API server host
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # ========== Logging Settings ==========
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/app/data/logs"  # Docker 挂载到 SSD
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
