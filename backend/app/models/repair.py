from datetime import datetime, timezone

from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.repair_status import RepairStatus
from app.enums.owner_type import OwnerType


class Repair(Base):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    bike_id: Mapped[int] = mapped_column(
        ForeignKey("bikes.id")
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("people.id")
    )

    problem_description: Mapped[str] = mapped_column(
        Text
    )

    status: Mapped[RepairStatus] = mapped_column(
        Enum(RepairStatus),
        default=RepairStatus.NEW,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    bike = relationship(
        "Bike",
        back_populates="repairs",
    )

    client = relationship(
        "Person",
        back_populates="repairs",
    )

    repair_services = relationship(
        "RepairService",
        back_populates="repair",
        cascade="all, delete-orphan",
    )

    repair_parts = relationship(
        "RepairPart",
        back_populates="repair",
        cascade="all, delete-orphan",
    )


class RepairService(Base):
    """Услуга в рамках конкретного ремонта.
    Цена может быть скорректирована вручную относительно базовой цены услуги.
    """
    __tablename__ = "repair_services"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    repair_id: Mapped[int] = mapped_column(
        ForeignKey("repairs.id")
    )

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id")
    )

    price: Mapped[float] = mapped_column(
        Float,
        comment="Цена за эту услугу в данном ремонте (может отличаться от базовой)",
    )

    repair = relationship(
        "Repair",
        back_populates="repair_services",
    )

    service = relationship(
        "Service",
        back_populates="repair_services",
    )


class RepairPart(Base):
    """Запчасть в рамках конкретного ремонта.
    При добавлении — автоматически списывается с остатка Part.quantity.
    """
    __tablename__ = "repair_parts"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    repair_id: Mapped[int] = mapped_column(
        ForeignKey("repairs.id")
    )

    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id")
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    purchase_price: Mapped[float] = mapped_column(
        Float,
        comment="Закупочная стоимость на момент добавления в ремонт",
    )

    sale_price: Mapped[float] = mapped_column(
        Float,
        comment="Цена продажи клиенту на момент добавления в ремонт",
    )

    owner: Mapped[OwnerType] = mapped_column(
        Enum(OwnerType),
        comment="Принадлежность запчасти: Кирилл или Виталий",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    repair = relationship(
        "Repair",
        back_populates="repair_parts",
    )

    part = relationship(
        "Part",
        back_populates="repair_parts",
    )