from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.person_status import PersonStatus


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    first_name: Mapped[str] = mapped_column(
        String(100)
    )

    last_name: Mapped[str] = mapped_column(
        String(100)
    )

    middle_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    telegram: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[PersonStatus] = mapped_column(
        Enum(PersonStatus),
        default=PersonStatus.ACTIVE,
    )

    repairs = relationship(
        "Repair",
        back_populates="client",
    )

    rentals = relationship(
        "Rental",
        back_populates="person",
    )

    photos = relationship(
        "Photo",
        back_populates="person",
    )

    passport = relationship(
        "PassportData",
        back_populates="person",
        uselist=False,
    )

    person_tags = relationship(
        "PersonTag",
        back_populates="person",
        cascade="all, delete-orphan",
    )

    @property
    def tags(self) -> list[str]:
        """Названия тегов клиента. Требует, чтобы person_tags.tag были
        загружены заранее (selectinload), иначе в async-контексте
        обращение к ленивой связи упадёт с ошибкой."""
        return [pt.tag.name for pt in self.person_tags]