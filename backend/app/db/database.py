from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings


# Единый источник правды для DATABASE_URL — pydantic Settings (core/config.py),
# который читает .env / переменные окружения. Раньше здесь использовался
# os.getenv("DATABASE_URL") напрямую, из-за чего значение могло разойтись
# с тем, что видят остальные части приложения (например Settings.DATABASE_URL).
DATABASE_URL = settings.DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    echo=settings.SQL_ECHO,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)