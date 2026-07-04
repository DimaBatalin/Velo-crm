from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db

from app.enums.bike_owner_type import BikeOwnerType
from app.enums.bike_status import BikeStatus
from app.enums.bike_type import BikeType
from app.models.bike import Bike
from app.models.rental import Rental
from app.schemas.bike import BikeCreate, BikeResponse, BikeUpdate


router = APIRouter(
    prefix="/bikes",
    tags=["Bikes"],
)


def _bike_details_query():
    return select(Bike).options(
        selectinload(Bike.rentals).selectinload(Rental.person)
    )


@router.post(
    "",
    response_model=BikeResponse,
    status_code=201,
)
async def create_bike(
        bike_data: BikeCreate,
        db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Bike).where(Bike.serial_number == bike_data.serial_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Велосипед с таким номером рамы уже существует",
        )

    bike = Bike(**bike_data.model_dump())

    db.add(bike)
    await db.commit()

    result = await db.execute(
        _bike_details_query().where(Bike.id == bike.id)
    )
    return result.scalar_one()


@router.get(
    "",
    response_model=list[BikeResponse],
)
async def get_bikes(
        search: str | None = Query(None, description="Поиск по VIN, марке, модели"),
        status: BikeStatus | None = None,
        bike_type: BikeType | None = None,
        owner_type: BikeOwnerType | None = None,
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    query = _bike_details_query()

    if search:
        query = query.where(
            or_(
                Bike.serial_number.ilike(f"%{search}%"),
                Bike.brand.ilike(f"%{search}%"),
                Bike.model.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.where(Bike.status == status)

    if bike_type:
        query = query.where(Bike.type == bike_type)

    if owner_type:
        query = query.where(Bike.owner_type == owner_type)

    query = query.order_by(Bike.id.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/{bike_id}",
    response_model=BikeResponse,
)
async def get_bike(
        bike_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        _bike_details_query().where(Bike.id == bike_id)
    )

    bike = result.scalar_one_or_none()

    if not bike:
        raise HTTPException(
            status_code=404,
            detail="Bike not found",
        )

    return bike


@router.put(
    "/{bike_id}",
    response_model=BikeResponse,
)
async def update_bike(
        bike_id: int,
        bike_data: BikeUpdate,
        db: AsyncSession = Depends(get_db),
):
    bike = await db.get(Bike, bike_id)

    if not bike:
        raise HTTPException(
            status_code=404,
            detail="Bike not found",
        )

    update_data = bike_data.model_dump(exclude_unset=True)

    if "serial_number" in update_data and update_data["serial_number"] != bike.serial_number:
        existing = await db.execute(
            select(Bike).where(Bike.serial_number == update_data["serial_number"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Велосипед с таким номером рамы уже существует",
            )

    for field, value in update_data.items():
        setattr(bike, field, value)

    await db.commit()

    result = await db.execute(
        _bike_details_query().where(Bike.id == bike.id)
    )
    return result.scalar_one()


@router.delete("/{bike_id}")
async def delete_bike(
        bike_id: int,
        db: AsyncSession = Depends(get_db),
):
    bike = await db.get(Bike, bike_id)

    if not bike:
        raise HTTPException(
            status_code=404,
            detail="Bike not found",
        )

    await db.delete(bike)
    await db.commit()

    return {"message": "Bike deleted"}
