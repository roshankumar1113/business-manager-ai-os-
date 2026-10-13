"""
Business Manager — Application Configuration
All settings loaded from environment variables / .env file.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./business_manager.db"

    # ── JWT Auth ──────────────────────────────────────────────────────────
    secret_key: str = "bm-change-this-secret-in-production-2026"
    algorithm: str = "HS256"
    access_token_minutes: int = 43200          # 30 days default

    # ── CORS ──────────────────────────────────────────────────────────────
    cors_origins: str = "*"                    # comma-separated in prod

    # ── Google Gemini AI ──────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout: int = 25

    # ── App Meta ──────────────────────────────────────────────────────────
    app_name: str = "Business Manager AI OS"
    app_version: str = "2.0.0"
    environment: str = "development"           # development | production

    # ── Subscription Plan Limits ──────────────────────────────────────────
    plan_free_businesses: int = 1
    plan_free_employees: int = 0
    plan_pro_businesses: int = 3
    plan_pro_employees: int = 3
    plan_business_businesses: int = 10
    plan_business_employees: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
