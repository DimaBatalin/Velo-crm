from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field
from pydantic import EmailStr
from pydantic import Field

from app.enums.person_status import PersonStatus
from app.enums.rental_status import RentalStatus
from app.schemas.compact import BikeMini
from app.schemas.compact import RentalForPerson


class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)

    middle_name: str | None = None

    phone: str = Field(..., min_length=1)

    email: EmailStr | None = None
    telegram: str | None = None
    notes: str | None = None


class PersonCreate(PersonBase):
    status: PersonStatus = PersonStatus.ACTIVE


class PersonUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1)
    last_name: str | None = Field(None, min_length=1)

    middle_name: str | None = None

    phone: str | None = Field(None, min_length=1)

    email: EmailStr | None = None
    telegram: str | None = None
    notes: str | None = None

    status: PersonStatus | None = None


class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str
    middle_name: str | None = None

    phone: str
    email: str | None = None
    telegram: str | None = None
    notes: str | None = None

    status: PersonStatus

    created_at: datetime
    updated_at: datetime

    rentals: list[RentalForPerson] = []

    tags: list[str] = Field(
        default_factory=list,
        description="Названия тегов, привязанных к клиенту",
    )

    @computed_field
    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part)

    @computed_field
    @property
    def current_bikes(self) -> list[BikeMini]:
        return [
            rental.bike
            for rental in self.rentals
            if rental.status == RentalStatus.ACTIVE and rental.bike is not None
        ]
