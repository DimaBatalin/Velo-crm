from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.enums.owner_type import OwnerType


class PartBase(BaseModel):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    category: str | None = Field(
        None,
        max_length=100,
    )

    sku: str | None = Field(
        None,
        max_length=100,
    )

    quantity: int = Field(
        0,
        ge=0,
    )

    purchase_price: float = Field(
        ...,
        ge=0,
    )

    sale_price: float = Field(
        ...,
        ge=0,
    )

    owner: OwnerType

    supplier: str | None = Field(
        None,
        max_length=255,
    )

    notes: str | None = None


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )

    category: str | None = None

    sku: str | None = None

    quantity: int | None = Field(
        None,
        ge=0,
    )

    purchase_price: float | None = Field(
        None,
        ge=0,
    )

    sale_price: float | None = Field(
        None,
        ge=0,
    )

    owner: OwnerType | None = None

    supplier: str | None = None

    notes: str | None = None


class PartResponse(PartBase):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime