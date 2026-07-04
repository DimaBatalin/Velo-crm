from sqlalchemy import String
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    file_path: Mapped[str] = mapped_column(
        String(500)
    )

    bike_id: Mapped[int | None] = mapped_column(
        ForeignKey("bikes.id"),
        nullable=True,
    )

    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("people.id"),
        nullable=True,
    )

    bike = relationship(
        "Bike",
        back_populates="photos",
    )

    person = relationship(
        "Person",
        back_populates="photos",
    )