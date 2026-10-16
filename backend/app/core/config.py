from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AI Recruitment Assistant"
    database_url: str = "sqlite:///./app.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: str = str(BACKEND_DIR / "uploads")
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    seed_demo_data: bool = True
    demo_admin_email: str = "admin@example.com"
    demo_admin_password: str = "admin123"

    @field_validator("database_url")
    @classmethod
    def resolve_sqlite_database_path(cls, value: str) -> str:
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value
        raw_path = value[len(prefix):]
        if raw_path == ":memory:":
            return value
        path = Path(raw_path)
        if path.is_absolute():
            return value
        return f"sqlite:///{(BACKEND_DIR / path).resolve().as_posix()}"

    @field_validator("upload_dir")
    @classmethod
    def resolve_upload_directory(cls, value: str) -> str:
        path = Path(value)
        return str(path if path.is_absolute() else (BACKEND_DIR.parent / path).resolve())

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
        protected_namespaces=("settings_",),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


BASE_DIR = BACKEND_DIR
UPLOAD_DIR = BACKEND_DIR / "uploads"
