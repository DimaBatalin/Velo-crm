from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db

from app.enums.person_status import PersonStatus
from app.models.person import Person
from app.models.rental import Rental
from app.schemas.person import PersonCreate, PersonResponse, PersonUpdate


router = APIRouter(
    prefix="/people",
    tags=["People"],
)


def _person_details_query():
    return select(Person).options(
        selectinload(Person.rentals).selectinload(Rental.bike)
    )


@router.post(
    "",
    response_model=PersonResponse,
    status_code=201,
)
async def create_person(
        person_data: PersonCreate,
        db: AsyncSession = Depends(get_db),
):
    existing_person = await db.execute(
        select(Person).where(Person.phone == person_data.phone)
    )

    if existing_person.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Phone already exists",
        )

    person = Person(**person_data.model_dump())

    db.add(person)
    await db.commit()

    result = await db.execute(
        _person_details_query().where(Person.id == person.id)
    )
    return result.scalar_one()


@router.get(
    "",
    response_model=list[PersonResponse],
)
async def get_people(
        search: str | None = None,
        status: PersonStatus | None = None,
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    query = _person_details_query()

    if search:
        query = query.where(
            or_(
                Person.first_name.ilike(f"%{search}%"),
                Person.last_name.ilike(f"%{search}%"),
                Person.phone.ilike(f"%{search}%"),
                Person.email.ilike(f"%{search}%"),
                Person.telegram.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.where(Person.status == status)

    query = query.order_by(Person.id.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/{person_id}",
    response_model=PersonResponse,
)
async def get_person(
        person_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        _person_details_query().where(Person.id == person_id)
    )

    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    return person


@router.put(
    "/{person_id}",
    response_model=PersonResponse,
)
async def update_person(
        person_id: int,
        person_data: PersonUpdate,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )

    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    for field, value in person_data.model_dump(exclude_unset=True).items():
        setattr(person, field, value)

    await db.commit()

    result = await db.execute(
        _person_details_query().where(Person.id == person.id)
    )
    return result.scalar_one()


@router.delete("/{person_id}")
async def delete_person(
        person_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )

    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    await db.delete(person)
    await db.commit()

    return {"message": "Person deleted"}
