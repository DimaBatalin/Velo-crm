from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field

from app.enums.rental_status import RentalStatus


class BikeMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_number: str
    brand: str | None = None
    model: str | None = None
    color: str | None = None


class PersonMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    middle_name: str | None = None
    phone: str

    @computed_field
    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part)


class RentalForPerson(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: RentalStatus
    started_at: datetime
    ended_at: datetime | None = None
    price_per_day: float | None = None
    bike: BikeMini


class RentalForBike(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: RentalStatus
    started_at: datetime
    ended_at: datetime | None = None
    price_per_day: float | None = None
    person: PersonMini
