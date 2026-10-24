"""Application configuration settings."""
import ssl
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_name: str = "Restaurant Order Management System"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False
    
    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "restaurant_db"
    db_user: str = "root"
    db_password: str = ""
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_ssl_ca: Optional[str] = None
    
    # JWT
    jwt_secret: str = "your-super-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    reload: bool = False
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Generate database URL."""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def database_url_async(self) -> str:
        """Generate async database URL."""
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def db_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Build an SSL context from the CA certificate, if configured."""
        if not self.db_ssl_ca:
            return None
        ca_path = Path(self.db_ssl_ca)
        if not ca_path.is_absolute():
            # settings.py lives at project/app/infrastructure/config/ -> project root is parents[3]
            ca_path = Path(__file__).resolve().parents[3] / ca_path
        context = ssl.create_default_context(cafile=str(ca_path))
        return context


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
