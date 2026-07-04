from datetime import date

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class PassportData(Base):
    __tablename__ = "passport_data"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id"),
        unique=True,
    )

    series: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    issued_by: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    issued_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    person = relationship(
        "Person",
        back_populates="passport",
    )