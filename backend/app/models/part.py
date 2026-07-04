from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.owner_type import OwnerType


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    purchase_price: Mapped[float] = mapped_column(
        Float,
        comment="Закупочная стоимость",
    )

    sale_price: Mapped[float] = mapped_column(
        Float,
        comment="Цена продажи клиенту",
    )

    owner: Mapped[OwnerType] = mapped_column(
        Enum(OwnerType),
        comment="Принадлежность: Кирилл или Виталий",
    )

    supplier: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Поставщик / источник",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    repair_parts = relationship(
        "RepairPart",
        back_populates="part",
    )