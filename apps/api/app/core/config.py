from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "LegalOS"
    app_env: str = "development"
    app_debug: bool = True
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    database_url: str = (
        "postgresql+asyncpg://legalos:legalos@localhost:5432/legalos"
    )
    database_echo: bool = False
    auto_create_db: bool = False
    auto_seed_demo: bool = False

    valkey_url: str = "redis://localhost:6379/0"
    local_storage_dir: Path = Path(".data/storage")
    max_upload_size_bytes: int = 25 * 1024 * 1024
    hybrid_embedding_dimensions: int = 16
    embedding_provider: str = "deterministic-local"
    reranker_provider: str = "deterministic-local"
    generation_provider: str = "deterministic-local"
    generation_model_name: str = "template-v1"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300

    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    cors_methods_raw: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        alias="CORS_METHODS",
    )
    cors_headers_raw: str = Field(
        default="Authorization,Content-Type,Accept",
        alias="CORS_HEADERS",
    )

    seed_data_path: Path = Path("../../tests/fixtures/seed_data.json")
    ocr_languages: str = "eng"
    ocr_tesseract_config: str = "--psm 6"
    ocr_pdf_render_dpi: int = 300
    ocr_min_extracted_text_chars: int = 32

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_methods(self) -> list[str]:
        return [item.strip() for item in self.cors_methods_raw.split(",") if item.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_headers(self) -> list[str]:
        return [item.strip() for item in self.cors_headers_raw.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> Settings:
        app_env = self.app_env.lower()
        if app_env not in {"development", "dev", "test"}:
            if self.jwt_secret == "change-me-in-production":
                raise ValueError("JWT_SECRET must be set outside development and test")
            if self.auto_create_db:
                raise ValueError("AUTO_CREATE_DB must be false outside development and test")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
