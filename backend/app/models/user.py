from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.enums.user_role import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.MECHANIC,
        server_default=UserRole.MECHANIC.value,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
