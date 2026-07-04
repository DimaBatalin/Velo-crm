from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class PassportBase(BaseModel):

    series: str | None = Field(
        None,
        max_length=10,
    )

    number: str | None = Field(
        None,
        max_length=20,
    )

    issued_by: str | None = Field(
        None,
        max_length=500,
    )

    issued_at: date | None = None

    notes: str | None = None


class PassportCreate(PassportBase):
    pass


class PassportUpdate(PassportBase):
    pass


class PassportResponse(PassportBase):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    person_id: int

    created_at: datetime

    updated_at: datetime