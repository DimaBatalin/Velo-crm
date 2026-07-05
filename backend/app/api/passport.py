from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.enums.user_role import UserRole

from app.models.passport import PassportData
from app.models.person import Person

from app.schemas.passport import PassportCreate
from app.schemas.passport import PassportUpdate
from app.schemas.passport import PassportResponse


router = APIRouter(
    prefix="/people/{person_id}/passport",
    tags=["Passport"],
)


async def _get_person_or_404(
        person_id: int,
        db: AsyncSession,
) -> Person:

    person = await db.get(Person, person_id)

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    return person


@router.get(
    "",
    response_model=PassportResponse,
)
async def get_passport(
        person_id: int,
        db: AsyncSession = Depends(get_db),
):
    await _get_person_or_404(person_id, db)

    result = await db.execute(
        select(PassportData).where(
            PassportData.person_id == person_id
        )
    )

    passport = result.scalar_one_or_none()

    if not passport:
        raise HTTPException(
            status_code=404,
            detail="Passport not found",
        )

    return passport


@router.post(
    "",
    response_model=PassportResponse,
    status_code=201,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
async def create_passport(
        person_id: int,
        passport_data: PassportCreate,
        db: AsyncSession = Depends(get_db),
):
    await _get_person_or_404(person_id, db)

    existing = await db.execute(
        select(PassportData).where(
            PassportData.person_id == person_id
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Passport already exists for this person",
        )

    passport = PassportData(
        person_id=person_id,
        **passport_data.model_dump(),
    )

    db.add(passport)

    await db.commit()

    await db.refresh(passport)

    return passport


@router.put(
    "",
    response_model=PassportResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
async def update_passport(
        person_id: int,
        passport_data: PassportUpdate,
        db: AsyncSession = Depends(get_db),
):
    await _get_person_or_404(person_id, db)

    result = await db.execute(
        select(PassportData).where(
            PassportData.person_id == person_id
        )
    )

    passport = result.scalar_one_or_none()

    if not passport:
        raise HTTPException(
            status_code=404,
            detail="Passport not found",
        )

    for field, value in passport_data.model_dump(exclude_unset=True).items():
        setattr(passport, field, value)

    await db.commit()

    await db.refresh(passport)

    return passport


@router.delete(
    "",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
)
async def delete_passport(
        person_id: int,
        db: AsyncSession = Depends(get_db),
):
    await _get_person_or_404(person_id, db)

    result = await db.execute(
        select(PassportData).where(
            PassportData.person_id == person_id
        )
    )

    passport = result.scalar_one_or_none()

    if not passport:
        raise HTTPException(
            status_code=404,
            detail="Passport not found",
        )

    await db.delete(passport)

    await db.commit()

    return {"message": "Passport deleted"}