from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

from app.enums.repair_status import RepairStatus
from app.enums.owner_type import OwnerType


# ──────────────────────────────────────────────
# RepairService schemas
# ──────────────────────────────────────────────

class RepairServiceAdd(BaseModel):
    """Добавить услугу в ремонт."""

    service_id: int

    price: float | None = Field(
        None,
        ge=0,
        description="Переопределить цену. Если None — берётся базовая цена услуги.",
    )


class RepairServiceResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    service_id: int

    service_name: str = Field(
        ...,
        description="Название услуги из справочника",
    )

    price: float

    @classmethod
    def from_orm_with_service(cls, repair_service) -> "RepairServiceResponse":
        return cls(
            id=repair_service.id,
            service_id=repair_service.service_id,
            service_name=repair_service.service.name,
            price=repair_service.price,
        )


# ──────────────────────────────────────────────
# RepairPart schemas
# ──────────────────────────────────────────────

class RepairPartAdd(BaseModel):
    """Добавить запчасть в ремонт."""

    part_id: int

    quantity: int = Field(
        1,
        ge=1,
    )

    sale_price: float | None = Field(
        None,
        ge=0,
        description="Переопределить цену продажи. Если None — берётся цена из карточки запчасти.",
    )

    notes: str | None = None


class RepairPartResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    part_id: int

    part_name: str = Field(
        ...,
        description="Название запчасти",
    )

    quantity: int

    purchase_price: float

    sale_price: float

    owner: OwnerType

    notes: str | None = None

    @classmethod
    def from_orm_with_part(cls, repair_part) -> "RepairPartResponse":
        return cls(
            id=repair_part.id,
            part_id=repair_part.part_id,
            part_name=repair_part.part.name,
            quantity=repair_part.quantity,
            purchase_price=repair_part.purchase_price,
            sale_price=repair_part.sale_price,
            owner=repair_part.owner,
            notes=repair_part.notes,
        )


# ──────────────────────────────────────────────
# Финансовое summary
# ──────────────────────────────────────────────

class OwnerSummary(BaseModel):
    """Итог по одному владельцу запчастей."""

    parts_cost: float = Field(
        description="Закупочная стоимость запчастей",
    )

    parts_revenue: float = Field(
        description="Выручка от продажи запчастей клиенту",
    )

    parts_profit: float = Field(
        description="Прибыль с запчастей (revenue - cost)",
    )


class RepairFinancialSummary(BaseModel):
    """Финансовый итог по ремонту."""

    services_total: float = Field(
        description="Сумма всех услуг",
    )

    parts_total: float = Field(
        description="Сумма запчастей для клиента",
    )

    total_for_client: float = Field(
        description="Итого к оплате клиентом",
    )

    kirill: OwnerSummary

    vitaly: OwnerSummary


# ──────────────────────────────────────────────
# Repair schemas
# ──────────────────────────────────────────────

class RepairCreate(BaseModel):

    bike_id: int

    client_id: int

    problem_description: str = Field(
        ...,
        min_length=1,
    )


class RepairUpdate(BaseModel):

    problem_description: str | None = Field(
        None,
        min_length=1,
    )

    status: RepairStatus | None = None


class RepairResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    bike_id: int

    client_id: int

    problem_description: str

    status: RepairStatus

    started_at: datetime

    completed_at: datetime | None = None

    created_at: datetime

    updated_at: datetime


class RepairDetailResponse(RepairResponse):
    """Ремонт с вложенными услугами и запчастями."""

    services: list[RepairServiceResponse] = []

    parts: list[RepairPartResponse] = []