from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.database import engine


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create first admin user if no users exist
    from app.db.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import hash_password
    from app.core.config import settings

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        if result.first() is None:
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name=settings.FIRST_ADMIN_NAME,
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            )
            db.add(admin)
            await db.commit()
            print(f"[init_db] Created admin user: {settings.FIRST_ADMIN_EMAIL}")
