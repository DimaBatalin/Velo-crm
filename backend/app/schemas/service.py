from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ServiceBase(BaseModel):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    price: float = Field(
        ...,
        ge=0,
    )


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    price: float | None = Field(
        None,
        ge=0,
    )


class ServiceResponse(ServiceBase):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime