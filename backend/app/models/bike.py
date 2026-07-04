from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.bike_status import BikeStatus
from app.enums.bike_type import BikeType
from app.enums.bike_owner_type import BikeOwnerType


class Bike(Base):
    __tablename__ = "bikes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    type: Mapped[BikeType] = mapped_column(
        Enum(BikeType),
        nullable=False,
        index=True,
        default=BikeType.ELECTRO,
        comment="Тип велосипеда: электро или механический",
    )

    owner_type: Mapped[BikeOwnerType | None] = mapped_column(
        Enum(BikeOwnerType),
        nullable=True,
        comment="Кому принадлежит велосипед (арендодатель): ВМ или Виталий",
    )

    serial_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="VIN / номер рамы — обязательное уникальное поле",
    )

    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[BikeStatus] = mapped_column(
        Enum(BikeStatus),
        default=BikeStatus.READY,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    repairs = relationship(
        "Repair",
        back_populates="bike",
    )

    rentals = relationship(
        "Rental",
        back_populates="bike",
    )

    photos = relationship(
        "Photo",
        back_populates="bike",
    )
