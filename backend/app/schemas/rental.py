from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

from app.enums.rental_status import RentalStatus


class RentalCreate(BaseModel):

    bike_id: int

    person_id: int

    price_per_day: float | None = Field(
        None,
        ge=0,
    )


class RentalUpdate(BaseModel):

    bike_id: int | None = None

    person_id: int | None = None

    started_at: datetime | None = None

    ended_at: datetime | None = None

    status: RentalStatus | None = None

    price_per_day: float | None = Field(
        None,
        ge=0,
    )


class RentalClose(BaseModel):
    """Закрыть аренду — зафиксировать время возврата."""

    ended_at: datetime | None = Field(
        None,
        description="Если не передано — проставляется текущее время",
    )


class RentalResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    bike_id: int

    person_id: int

    started_at: datetime

    ended_at: datetime | None = None

    price_per_day: float | None = None

    status: RentalStatus

    created_at: datetime

    updated_at: datetime

    @computed_field
    @property
    def days(self) -> int | None:
        """Количество дней аренды. None если аренда ещё активна."""
        if not self.ended_at:
            return None
        delta = self.ended_at - self.started_at
        return max(delta.days, 1)

    @computed_field
    @property
    def total_cost(self) -> float | None:
        """Итоговая стоимость. None если нет цены или аренда не закрыта."""
        if self.price_per_day is None or self.days is None:
            return None
        return round(self.price_per_day * self.days, 2)