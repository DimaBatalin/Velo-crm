from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import select
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.models.part import Part

from app.enums.owner_type import OwnerType

from app.schemas.part import PartCreate
from app.schemas.part import PartUpdate
from app.schemas.part import PartResponse


router = APIRouter(
    prefix="/parts",
    tags=["Parts"],
)


@router.post(
    "",
    response_model=PartResponse,
    status_code=201,
)
async def create_part(
        part_data: PartCreate,
        db: AsyncSession = Depends(get_db),
):
    part = Part(**part_data.model_dump())

    db.add(part)

    await db.commit()

    await db.refresh(part)

    return part


@router.get(
    "",
    response_model=list[PartResponse],
)
async def get_parts(
        search: str | None = None,
        category: str | None = None,
        owner: OwnerType | None = None,
        low_stock: bool = False,
        low_stock_threshold: int = Query(default=3, ge=0),
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    query = select(Part)

    if search:
        query = query.where(
            or_(
                Part.name.ilike(f"%{search}%"),
                Part.sku.ilike(f"%{search}%"),
                Part.supplier.ilike(f"%{search}%"),
            )
        )

    if category:
        query = query.where(
            Part.category.ilike(f"%{category}%")
        )

    if owner:
        query = query.where(
            Part.owner == owner
        )

    if low_stock:
        query = query.where(
            Part.quantity <= low_stock_threshold
        )

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)

    return result.scalars().all()


@router.get(
    "/{part_id}",
    response_model=PartResponse,
)
async def get_part(
        part_id: int,
        db: AsyncSession = Depends(get_db),
):
    part = await db.get(Part, part_id)

    if not part:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    return part


@router.put(
    "/{part_id}",
    response_model=PartResponse,
)
async def update_part(
        part_id: int,
        part_data: PartUpdate,
        db: AsyncSession = Depends(get_db),
):
    part = await db.get(Part, part_id)

    if not part:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    for field, value in part_data.model_dump(exclude_unset=True).items():
        setattr(part, field, value)

    await db.commit()

    await db.refresh(part)

    return part


@router.delete("/{part_id}")
async def delete_part(
        part_id: int,
        db: AsyncSession = Depends(get_db),
):
    part = await db.get(Part, part_id)

    if not part:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    await db.delete(part)

    await db.commit()

    return {"message": "Part deleted"}