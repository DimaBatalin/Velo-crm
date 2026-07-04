from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Float

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.rental_status import RentalStatus


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    bike_id: Mapped[int] = mapped_column(
        ForeignKey("bikes.id")
    )

    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id")
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    price_per_day: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Стоимость аренды в день",
    )

    status: Mapped[RentalStatus] = mapped_column(
        Enum(RentalStatus),
        default=RentalStatus.ACTIVE,
    )

    bike = relationship(
        "Bike",
        back_populates="rentals",
    )

    person = relationship(
        "Person",
        back_populates="rentals",
    )