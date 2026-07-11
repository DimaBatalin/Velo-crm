from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles
from app.enums.user_role import UserRole
from app.models.user import User

from app.models.bike import Bike
from app.models.person import Person
from app.models.rental import Rental

from app.enums.bike_status import BikeStatus
from app.enums.person_status import PersonStatus
from app.enums.rental_status import RentalStatus

from app.schemas.rental import RentalClose
from app.schemas.rental import RentalCreate
from app.schemas.rental import RentalResponse
from app.schemas.rental import RentalUpdate


router = APIRouter(
    prefix="/rentals",
    tags=["Rentals"],
)


async def _get_rental_or_404(
        rental_id: int,
        db: AsyncSession,
) -> Rental:

    rental = await db.get(Rental, rental_id)

    if not rental:
        raise HTTPException(
            status_code=404,
            detail="Rental not found",
        )

    return rental


_PERSON_STATUS_RU = {
    PersonStatus.BLOCKED: "заблокирован",
    PersonStatus.ARCHIVED: "в архиве",
    PersonStatus.FIRED: "уволен",
}


def _ensure_person_can_rent(person: Person) -> None:
    """Аренду можно оформлять только на активного клиента."""
    if person.status != PersonStatus.ACTIVE:
        status_ru = _PERSON_STATUS_RU.get(person.status, person.status.value)
        raise HTTPException(
            status_code=409,
            detail=f"Нельзя оформить аренду: клиент {status_ru}",
        )


def _release_bike_after_rental(bike: Bike | None) -> None:
    """Вернуть велосипед в READY, но только если он сейчас числится в аренде.
    Если за время аренды его перевели в ремонт или пометили украденным —
    этот статус важнее и затирать его нельзя."""
    if bike and bike.status == BikeStatus.RENTED:
        bike.status = BikeStatus.READY


# ──────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────

@router.post(
    "",
    response_model=RentalResponse,
    status_code=201,
)
async def create_rental(
        rental_data: RentalCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    bike = await db.get(Bike, rental_data.bike_id)

    if not bike:
        raise HTTPException(
            status_code=404,
            detail="Bike not found",
        )

    if bike.status == BikeStatus.RENTED:
        raise HTTPException(
            status_code=409,
            detail="Велосипед уже в аренде",
        )

    if bike.status == BikeStatus.REPAIR:
        raise HTTPException(
            status_code=409,
            detail="Велосипед в ремонте — сначала завершите ремонт",
        )

    if bike.status == BikeStatus.STOLEN:
        raise HTTPException(
            status_code=409,
            detail="Велосипед числится украденным — аренда невозможна",
        )

    person = await db.get(Person, rental_data.person_id)

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    _ensure_person_can_rent(person)

    rental = Rental(
        **rental_data.model_dump(),
        created_by_user_id=current_user.id,
    )

    # Переводим велосипед в статус "в аренде"
    bike.status = BikeStatus.RENTED

    db.add(rental)

    await db.commit()

    await db.refresh(rental)

    return rental


@router.get(
    "",
    response_model=list[RentalResponse],
)
async def get_rentals(
        bike_id: int | None = None,
        person_id: int | None = None,
        status: RentalStatus | None = None,
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    query = select(Rental)

    if bike_id:
        query = query.where(Rental.bike_id == bike_id)

    if person_id:
        query = query.where(Rental.person_id == person_id)

    if status:
        query = query.where(Rental.status == status)

    query = query.order_by(Rental.started_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)

    return result.scalars().all()


@router.get(
    "/{rental_id}",
    response_model=RentalResponse,
)
async def get_rental(
        rental_id: int,
        db: AsyncSession = Depends(get_db),
):
    return await _get_rental_or_404(rental_id, db)


@router.put(
    "/{rental_id}",
    response_model=RentalResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
async def update_rental(
        rental_id: int,
        rental_data: RentalUpdate,
        db: AsyncSession = Depends(get_db),
):
    rental = await _get_rental_or_404(rental_id, db)

    if rental_data.person_id and rental_data.person_id != rental.person_id:

        person = await db.get(Person, rental_data.person_id)

        if not person:
            raise HTTPException(
                status_code=404,
                detail="Person not found",
            )

        _ensure_person_can_rent(person)

        rental.person_id = rental_data.person_id

    if rental_data.bike_id and rental_data.bike_id != rental.bike_id:

        new_bike = await db.get(Bike, rental_data.bike_id)

        if not new_bike:
            raise HTTPException(
                status_code=404,
                detail="Bike not found",
            )

        if new_bike.status != BikeStatus.READY:
            raise HTTPException(
                status_code=409,
                detail="Велосипед недоступен для аренды",
            )

        old_bike = await db.get(Bike, rental.bike_id)

        _release_bike_after_rental(old_bike)

        new_bike.status = BikeStatus.RENTED

        rental.bike_id = rental_data.bike_id
    if rental_data.started_at is not None:
        rental.started_at = rental_data.started_at

    if rental_data.ended_at is not None:
        rental.ended_at = rental_data.ended_at

    if rental_data.price_per_day is not None:
        rental.price_per_day = rental_data.price_per_day

    if rental_data.status is not None:
        rental.status = rental_data.status

    await db.commit()

    await db.refresh(rental)

    return rental


# ──────────────────────────────────────────────
# Закрытие аренды
# ──────────────────────────────────────────────

@router.post(
    "/{rental_id}/close",
    response_model=RentalResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
async def close_rental(
        rental_id: int,
        data: RentalClose = RentalClose(),
        db: AsyncSession = Depends(get_db),
):
    rental = await _get_rental_or_404(rental_id, db)

    if rental.status != RentalStatus.ACTIVE:
        raise HTTPException(
            status_code=409,
            detail=f"Rental is already {rental.status.value}",
        )

    rental.ended_at = data.ended_at or datetime.now(timezone.utc)
    rental.status = RentalStatus.RETURNED

    # Возвращаем велосипед в статус "готов" (если он не в ремонте/украден)
    bike = await db.get(Bike, rental.bike_id)

    _release_bike_after_rental(bike)

    await db.commit()

    await db.refresh(rental)

    return rental


@router.delete(
    "/{rental_id}",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
async def delete_rental(
        rental_id: int,
        db: AsyncSession = Depends(get_db),
):
    rental = await _get_rental_or_404(rental_id, db)

    # Если аренда активна — возвращаем велосипед (если он числится в аренде)
    if rental.status == RentalStatus.ACTIVE:
        bike = await db.get(Bike, rental.bike_id)
        _release_bike_after_rental(bike)

    await db.delete(rental)

    await db.commit()

    return {"message": "Rental deleted"}