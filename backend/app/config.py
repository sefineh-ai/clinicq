from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "clinicq.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            str(ROOT_DIR / ".env"),
            str(BASE_DIR / ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "ClinicQ - Appointment & Queue System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5434
    POSTGRES_USER: str = "clinicq_user"
    POSTGRES_PASSWORD: str = "clinicq_password"
    POSTGRES_DB: str = "clinicq_db"
    DATABASE_URL: str | None = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"
    ASYNC_DATABASE_URL: str | None = None

    @property
    def sync_database_uri(self) -> str:
        if self.DATABASE_URL:
            if "sqlite" in self.DATABASE_URL:
                url = self.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
                if "///./" in url:
                    url = url.replace("///./", f"///{DEFAULT_SQLITE_PATH.parent}/")
                return url
            # ensure psycopg2 or standard postgresql driver
            url = self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            return url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_uri(self) -> str:
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        if self.DATABASE_URL:
            if "sqlite" in self.DATABASE_URL:
                url = self.DATABASE_URL
                if not url.startswith("sqlite+aiosqlite://"):
                    url = url.replace("sqlite://", "sqlite+aiosqlite://")
                if "///./" in url:
                    url = url.replace("///./", f"///{DEFAULT_SQLITE_PATH.parent}/")
                return url
            if "asyncpg" in self.DATABASE_URL:
                return self.DATABASE_URL
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT Authentication
    SECRET_KEY: str = "clinicq-ultra-secure-jwt-secret-key-32chars-minimum-prod"
    ALGORITHM: str = "HS256"
    JWT_SECRET: str = "clinicq-ultra-secure-jwt-secret-key-32chars-minimum-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7    # 7 days

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    # No-show evening background job
    NO_SHOW_CHECK_INTERVAL_MINUTES: int = 60
    NO_SHOW_CUTOFF_HOUR_UTC: int = 20  # 8 PM UTC by default


settings = Settings()
