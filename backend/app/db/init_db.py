from sqlalchemy import select


async def create_tables():
    """
    Схема БД управляется исключительно через Alembic-миграции
    (см. `alembic upgrade head`). Здесь мы больше НЕ вызываем
    Base.metadata.create_all — иначе схема из моделей и история
    миграций могут разойтись.

    Единственное, что делаем на старте — создаём первого admin-
    пользователя, если таблица users пуста.
    """
    from app.db.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.config import settings
    from app.enums.user_role import UserRole

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        if result.first() is None:
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name=settings.FIRST_ADMIN_NAME,
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.commit()
            print(f"[init_db] Created admin user: {settings.FIRST_ADMIN_EMAIL}")
