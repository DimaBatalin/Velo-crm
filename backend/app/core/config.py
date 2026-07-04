from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env has highest priority → then environment variables → then defaults below
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,   # DATABASE_URL == database_url in .env
        extra="ignore",         # ignore unknown keys in .env
    )

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # ── First admin (created on startup if users table is empty) ──
    FIRST_ADMIN_EMAIL: str = "admin@velo.local"
    FIRST_ADMIN_PASSWORD: str = "changeme"
    FIRST_ADMIN_NAME: str = "Admin"


settings = Settings()
