from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import select
from sqlalchemy import or_
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_roles
from app.enums.user_role import UserRole

from app.models.part import Part

from app.enums.owner_type import OwnerType

from app.schemas.part import PartCreate
from app.schemas.part import PartUpdate
from app.schemas.part import PartResponse


router = APIRouter(
    prefix="/parts",
    tags=["Parts"],
)


async def _find_mergeable_part(
        part_data: PartCreate,
        db: AsyncSession,
) -> Part | None:
    """Ищет позицию, которую новая поставка должна пополнить, а не продублировать.

    Совпадать должны название (без учёта регистра и краевых пробелов),
    обе цены (до копейки) и владелец. Категория, артикул, поставщик,
    заметки и мин. остаток на слияние не влияют.

    Цены сверяем в Python, а не в SQL: round() по float-колонке в разных
    СУБД ведёт себя по-разному, а кандидатов с одинаковым названием и
    владельцем всегда единицы.
    """
    query = (
        select(Part)
        .where(
            func.lower(func.trim(Part.name)) == part_data.name.strip().lower(),
            Part.owner == part_data.owner,
        )
        .order_by(Part.id)
    )

    result = await db.execute(query)

    for candidate in result.scalars().all():
        if round(candidate.purchase_price, 2) != round(part_data.purchase_price, 2):
            continue

        if round(candidate.sale_price, 2) != round(part_data.sale_price, 2):
            continue

        return candidate

    return None


@router.post(
    "",
    response_model=PartResponse,
    status_code=201,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def create_part(
        part_data: PartCreate,
        db: AsyncSession = Depends(get_db),
):
    existing = await _find_mergeable_part(part_data, db)

    # Та же номенклатура по той же цене — пополняем остаток существующей
    # позиции, а не заводим на складе второй ряд «Камера 29».
    if existing:
        existing.quantity += part_data.quantity

        # Пустые справочные поля дозаполняем данными новой поставки,
        # уже заполненные не перетираем.
        for field in ("category", "sku", "supplier"):
            incoming = getattr(part_data, field)

            if incoming and not getattr(existing, field):
                setattr(existing, field, incoming)

        await db.commit()

        await db.refresh(existing)

        return existing

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
            Part.quantity <= Part.min_stock
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
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
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


@router.delete(
    "/{part_id}",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
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