from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

from app.enums.bike_status import BikeStatus
from app.enums.bike_type import BikeType
from app.enums.bike_owner_type import BikeOwnerType
from app.enums.rental_status import RentalStatus
from app.schemas.compact import PersonMini
from app.schemas.compact import RentalForBike


class BikeBase(BaseModel):
    type: BikeType = BikeType.ELECTRO

    owner_type: BikeOwnerType | None = None

    serial_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="VIN / номер рамы — обязательное уникальное поле",
    )

    brand: str | None = Field(None, max_length=100)

    model: str | None = Field(None, max_length=100)

    color: str | None = Field(None, max_length=50)

    notes: str | None = None


class BikeCreate(BikeBase):
    status: BikeStatus = BikeStatus.READY


class BikeUpdate(BaseModel):
    type: BikeType | None = None

    owner_type: BikeOwnerType | None = None

    serial_number: str | None = Field(None, min_length=1, max_length=100)

    brand: str | None = Field(None, max_length=100)

    model: str | None = Field(None, max_length=100)

    color: str | None = None

    status: BikeStatus | None = None

    notes: str | None = None


class BikeResponse(BikeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    status: BikeStatus

    created_at: datetime
    updated_at: datetime

    rentals: list[RentalForBike] = []

    @computed_field
    @property
    def current_people(self) -> list[PersonMini]:
        return [
            rental.person
            for rental in self.rentals
            if rental.status == RentalStatus.ACTIVE and rental.person is not None
        ]
