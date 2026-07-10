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

    # Log every SQL statement. Debugging only — very noisy in production.
    SQL_ECHO: bool = False

    # ── Proxy ─────────────────────────────────────────────────
    # Prefix that nginx strips before forwarding (e.g. "/api"). Empty when the
    # app is reached directly. FastAPI uses it to build correct openapi/docs URLs.
    ROOT_PATH: str = ""

    # ── CORS ──────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # ── First admin (created on startup if users table is empty) ──
    FIRST_ADMIN_EMAIL: str = "admin@velo.local"
    FIRST_ADMIN_PASSWORD: str = "changeme"
    FIRST_ADMIN_NAME: str = "Admin"


settings = Settings()
