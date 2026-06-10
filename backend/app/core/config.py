import os
import json
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_DIR / ".env"), str(BASE_DIR / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DeepResearch Agent"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/deepresearch"

    # Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # Security
    encryption_key: str = "CHANGE_ME_32BYTE_ENCRYPTION_KEY!!"

    # JWT
    jwt_secret_key: str = "CHANGE_ME_JWT_SECRET_KEY_AT_LEAST_32_CHARS!"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # CORS (JSON array string, e.g. ["http://localhost:3000"])
    cors_origins_raw: str = Field(
        default='["http://localhost:3000","http://127.0.0.1:3000"]',
        validation_alias="CORS_ORIGINS",
    )
    cors_origin_regex: str = (
        r"^https?://("
        r"localhost|"
        r"127\.0\.0\.1|"
        r"\[::1\]|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?$"
    )

    # Upload
    upload_dir: Path = BASE_DIR / "uploads"
    max_file_size_mb: int = 50

    # Tavily
    tavily_api_key: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 30

    @property
    def cors_origins(self) -> list[str]:
        try:
            origins = json.loads(self.cors_origins_raw)
            if isinstance(origins, str):
                return [origins]
            return origins
        except Exception:
            origins = [
                origin.strip()
                for origin in self.cors_origins_raw.split(",")
                if origin.strip()
            ]
            return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
