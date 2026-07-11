from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.core.deps import require_roles
from app.enums.user_role import UserRole

from sqlalchemy import delete as sa_delete

from app.enums.person_status import PersonStatus
from app.models.passport import PassportData
from app.models.person import Person
from app.models.photo import Photo
from app.models.rental import Rental
from app.models.repair import Repair
from app.models.tag import PersonTag, Tag
from app.schemas.person import PersonCreate, PersonResponse, PersonUpdate
from app.schemas.tag import PersonTagAdd


router = APIRouter(
    prefix="/people",
    tags=["People"],
)


def _person_details_query():
    return select(Person).options(
        selectinload(Person.rentals).selectinload(Rental.bike),
        selectinload(Person.person_tags).selectinload(PersonTag.tag),
        selectinload(Person.passport),
    )


@router.post(
    "",
    response_model=PersonResponse,
    status_code=201,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
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
        tag: str | None = Query(default=None, description="Фильтр по названию тега, напр. 'Магнит'"),
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    query = _person_details_query()

    if tag:
        query = query.join(Person.person_tags).join(PersonTag.tag).where(Tag.name == tag)

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
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
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


@router.delete(
    "/{person_id}",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
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

    # Аренды и ремонты — история, каскада на них нет: раньше удаление
    # клиента с историей падало с 500 (нарушение FK). Отвечаем 409.
    has_rental = await db.execute(
        select(Rental.id).where(Rental.person_id == person_id).limit(1)
    )
    has_repair = await db.execute(
        select(Repair.id).where(Repair.client_id == person_id).limit(1)
    )
    if has_rental.first() or has_repair.first():
        raise HTTPException(
            status_code=409,
            detail=(
                "У клиента есть аренды или ремонты — удаление сотрёт историю. "
                "Вместо удаления переведите его в статус «Архивирован» или «Уволен»."
            ),
        )

    # Паспорт и фото — не история, а атрибуты клиента: удаляем вместе с ним
    # (FK без каскада, иначе удаление упадёт).
    await db.execute(sa_delete(PassportData).where(PassportData.person_id == person_id))
    await db.execute(sa_delete(Photo).where(Photo.person_id == person_id))

    await db.delete(person)
    await db.commit()

    return {"message": "Person deleted"}


# ──────────────────────────────────────────────
# Теги клиента
# ──────────────────────────────────────────────

@router.post(
    "/{person_id}/tags",
    response_model=PersonResponse,
    status_code=201,
)
async def add_tag_to_person(
        person_id: int,
        data: PersonTagAdd,
        db: AsyncSession = Depends(get_db),
):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    tag = await db.get(Tag, data.tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    existing = await db.execute(
        select(PersonTag).where(
            PersonTag.person_id == person_id,
            PersonTag.tag_id == data.tag_id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(PersonTag(person_id=person_id, tag_id=data.tag_id))
        await db.commit()

    result = await db.execute(
        _person_details_query().where(Person.id == person_id)
    )
    return result.scalar_one()


@router.delete(
    "/{person_id}/tags/{tag_id}",
    response_model=PersonResponse,
)
async def remove_tag_from_person(
        person_id: int,
        tag_id: int,
        db: AsyncSession = Depends(get_db),
):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    result = await db.execute(
        select(PersonTag).where(
            PersonTag.person_id == person_id,
            PersonTag.tag_id == tag_id,
        )
    )
    person_tag = result.scalar_one_or_none()

    if not person_tag:
        raise HTTPException(status_code=404, detail="Tag not attached to this person")

    await db.delete(person_tag)
    await db.commit()

    result = await db.execute(
        _person_details_query().where(Person.id == person_id)
    )
    return result.scalar_one()
