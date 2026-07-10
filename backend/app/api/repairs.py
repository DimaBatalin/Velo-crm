from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles
from app.enums.user_role import UserRole

from app.models.bike import Bike
from app.models.part import Part
from app.models.person import Person
from app.models.repair import Repair
from app.models.repair import RepairPart
from app.models.repair import RepairService
from app.models.service import Service
from app.models.user import User

from app.enums.owner_type import OwnerType
from app.enums.bike_status import BikeStatus
from app.enums.repair_status import RepairStatus

from app.schemas.repair import RepairCreate
from app.schemas.repair import RepairDetailResponse
from app.schemas.repair import RepairFinancialSummary
from app.schemas.repair import RepairPartAdd
from app.schemas.repair import RepairPartResponse
from app.schemas.repair import RepairResponse
from app.schemas.repair import RepairServiceAdd
from app.schemas.repair import RepairServiceResponse
from app.schemas.repair import RepairUpdate
from app.schemas.repair import OwnerSummary


router = APIRouter(
    prefix="/repairs",
    tags=["Repairs"],
)


# ──────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────

async def _get_repair_or_404(
        repair_id: int,
        db: AsyncSession,
        with_relations: bool = False,
) -> Repair:

    if with_relations:
        result = await db.execute(
            select(Repair)
            .options(
                selectinload(Repair.repair_services).selectinload(RepairService.service),
                selectinload(Repair.repair_parts).selectinload(RepairPart.part),
                selectinload(Repair.closed_by),
            )
            .where(Repair.id == repair_id)
        )
        repair = result.scalar_one_or_none()
    else:
        repair = await db.get(Repair, repair_id)

    if not repair:
        raise HTTPException(
            status_code=404,
            detail="Repair not found",
        )

    return repair


def _total_cost_subqueries():
    """
    Подзапросы суммы услуг и суммы запчастей (по sale_price) в разбивке
    по repair_id — используются через outerjoin, чтобы посчитать
    total_cost без N+1 запросов.
    """
    services_sq = (
        select(
            RepairService.repair_id.label("repair_id"),
            func.coalesce(func.sum(RepairService.price), 0).label("services_sum"),
        )
        .group_by(RepairService.repair_id)
        .subquery()
    )

    parts_sq = (
        select(
            RepairPart.repair_id.label("repair_id"),
            func.coalesce(func.sum(RepairPart.sale_price * RepairPart.quantity), 0).label("parts_sum"),
        )
        .group_by(RepairPart.repair_id)
        .subquery()
    )

    return services_sq, parts_sq


def _build_detail_response(repair: Repair, total_cost: float | None = None) -> RepairDetailResponse:
    if total_cost is None:
        # repair.repair_services / repair.repair_parts уже загружены через
        # selectinload — суммируем в Python без дополнительных запросов к БД.
        total_cost = sum(rs.price for rs in repair.repair_services) + sum(
            rp.sale_price * rp.quantity for rp in repair.repair_parts
        )

    return RepairDetailResponse(
        id=repair.id,
        bike_id=repair.bike_id,
        client_id=repair.client_id,
        problem_description=repair.problem_description,
        status=repair.status,
        started_at=repair.started_at,
        completed_at=repair.completed_at,
        closed_by_user_id=repair.closed_by_user_id,
        closed_by_name=repair.closed_by.full_name if repair.closed_by else None,
        total_cost=total_cost,
        created_at=repair.created_at,
        updated_at=repair.updated_at,
        services=[
            RepairServiceResponse.from_orm_with_service(rs)
            for rs in repair.repair_services
        ],
        parts=[
            RepairPartResponse.from_orm_with_part(rp)
            for rp in repair.repair_parts
        ],
    )


# ──────────────────────────────────────────────
# CRUD ремонтов
# ──────────────────────────────────────────────

@router.post(
    "",
    response_model=RepairResponse,
    status_code=201,
)
async def create_repair(
        repair_data: RepairCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC)),
):
    bike = await db.get(Bike, repair_data.bike_id)

    if not bike:
        raise HTTPException(
            status_code=404,
            detail="Bike not found",
        )

    client = await db.get(Person, repair_data.client_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    repair = Repair(
        **{**repair_data.model_dump(), "problem_description": repair_data.problem_description or ""},
        created_by_user_id=current_user.id,
    )

    db.add(repair)

    await db.commit()

    await db.refresh(repair)

    return repair


@router.get(
    "",
    response_model=list[RepairResponse],
)
async def get_repairs(
        bike_id: int | None = None,
        client_id: int | None = None,
        status: RepairStatus | None = None,
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    services_sq, parts_sq = _total_cost_subqueries()

    query = (
        select(
            Repair,
            (
                func.coalesce(services_sq.c.services_sum, 0)
                + func.coalesce(parts_sq.c.parts_sum, 0)
            ).label("total_cost"),
        )
        .outerjoin(services_sq, services_sq.c.repair_id == Repair.id)
        .outerjoin(parts_sq, parts_sq.c.repair_id == Repair.id)
        .options(selectinload(Repair.closed_by))
    )

    if bike_id:
        query = query.where(Repair.bike_id == bike_id)

    if client_id:
        query = query.where(Repair.client_id == client_id)

    if status:
        query = query.where(Repair.status == status)

    query = query.order_by(Repair.started_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)

    responses = []
    for repair, total_cost in result.all():
        responses.append(
            RepairResponse(
                id=repair.id,
                bike_id=repair.bike_id,
                client_id=repair.client_id,
                problem_description=repair.problem_description,
                status=repair.status,
                started_at=repair.started_at,
                completed_at=repair.completed_at,
                closed_by_user_id=repair.closed_by_user_id,
                closed_by_name=repair.closed_by.full_name if repair.closed_by else None,
                total_cost=float(total_cost),
                created_at=repair.created_at,
                updated_at=repair.updated_at,
            )
        )

    return responses


@router.get(
    "/{repair_id}",
    response_model=RepairDetailResponse,
)
async def get_repair(
        repair_id: int,
        db: AsyncSession = Depends(get_db),
):
    repair = await _get_repair_or_404(repair_id, db, with_relations=True)

    return _build_detail_response(repair)


@router.put(
    "/{repair_id}",
    response_model=RepairDetailResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def update_repair(
        repair_id: int,
        repair_data: RepairUpdate,
        db: AsyncSession = Depends(get_db),
):
    repair = await _get_repair_or_404(repair_id, db, with_relations=True)

    update_fields = repair_data.model_dump(exclude_unset=True)

    new_status = update_fields.get("status")

    # Фиксируем время завершения при переводе в done
    if new_status == RepairStatus.DONE and not repair.completed_at:
        if not update_fields.get("closed_by_user_id"):
            raise HTTPException(
                status_code=422,
                detail="closed_by_user_id обязателен при переводе ремонта в статус 'done'",
            )

        closer = await db.get(User, update_fields["closed_by_user_id"])
        if not closer:
            raise HTTPException(
                status_code=404,
                detail="User (closed_by_user_id) not found",
            )

        repair.completed_at = datetime.now(timezone.utc)

        bike = await db.get(Bike, repair.bike_id)
        if bike and bike.status == BikeStatus.REPAIR:
            bike.status = BikeStatus.READY

    # При отмене ремонта велосипед тоже нужно вернуть в строй,
    # иначе он "зависает" в статусе REPAIR
    elif new_status == RepairStatus.CANCELLED:
        bike = await db.get(Bike, repair.bike_id)
        if bike and bike.status == BikeStatus.REPAIR:
            bike.status = BikeStatus.READY

    for field, value in update_fields.items():
        setattr(repair, field, value)

    await db.commit()

    await db.refresh(repair)

    repair = await _get_repair_or_404(repair_id, db, with_relations=True)

    return _build_detail_response(repair)


@router.delete(
    "/{repair_id}",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def delete_repair(
        repair_id: int,
        db: AsyncSession = Depends(get_db),
):
    repair = await _get_repair_or_404(repair_id, db, with_relations=True)

    # Возвращаем запчасти на склад перед удалением
    for rp in repair.repair_parts:
        part = await db.get(Part, rp.part_id)
        if part:
            part.quantity += rp.quantity

    await db.delete(repair)

    await db.commit()

    return {"message": "Repair deleted"}


# ──────────────────────────────────────────────
# Услуги в ремонте
# ──────────────────────────────────────────────

@router.post(
    "/{repair_id}/services",
    response_model=RepairServiceResponse,
    status_code=201,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def add_service_to_repair(
        repair_id: int,
        data: RepairServiceAdd,
        db: AsyncSession = Depends(get_db),
):
    await _get_repair_or_404(repair_id, db)

    service = await db.get(Service, data.service_id)

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    # Если цена не передана — берём базовую из справочника
    price = data.price if data.price is not None else service.price

    repair_service = RepairService(
        repair_id=repair_id,
        service_id=data.service_id,
        price=price,
    )

    db.add(repair_service)

    await db.commit()

    await db.refresh(repair_service)

    # Подгружаем связь для ответа
    result = await db.execute(
        select(RepairService)
        .options(selectinload(RepairService.service))
        .where(RepairService.id == repair_service.id)
    )

    return RepairServiceResponse.from_orm_with_service(
        result.scalar_one()
    )


@router.delete(
    "/{repair_id}/services/{repair_service_id}",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def remove_service_from_repair(
        repair_id: int,
        repair_service_id: int,
        db: AsyncSession = Depends(get_db),
):
    await _get_repair_or_404(repair_id, db)

    result = await db.execute(
        select(RepairService).where(
            RepairService.id == repair_service_id,
            RepairService.repair_id == repair_id,
            )
    )

    repair_service = result.scalar_one_or_none()

    if not repair_service:
        raise HTTPException(
            status_code=404,
            detail="Service entry not found in this repair",
        )

    await db.delete(repair_service)

    await db.commit()

    return {"message": "Service removed from repair"}


# ──────────────────────────────────────────────
# Запчасти в ремонте (с автосписанием)
# ──────────────────────────────────────────────

@router.post(
    "/{repair_id}/parts",
    response_model=RepairPartResponse,
    status_code=201,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def add_part_to_repair(
        repair_id: int,
        data: RepairPartAdd,
        db: AsyncSession = Depends(get_db),
):
    await _get_repair_or_404(repair_id, db)

    part = await db.get(Part, data.part_id)

    if not part:
        raise HTTPException(
            status_code=404,
            detail="Part not found",
        )

    if part.quantity < data.quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Not enough stock: requested {data.quantity}, "
                f"available {part.quantity}"
            ),
        )

    # Фиксируем цены на момент добавления (снапшот)
    sale_price = data.sale_price if data.sale_price is not None else part.sale_price

    repair_part = RepairPart(
        repair_id=repair_id,
        part_id=data.part_id,
        quantity=data.quantity,
        purchase_price=part.purchase_price,
        sale_price=sale_price,
        owner=part.owner,
        notes=data.notes,
    )

    # Атомарное списание остатка
    part.quantity -= data.quantity

    db.add(repair_part)

    await db.commit()

    await db.refresh(repair_part)

    # Подгружаем связь для ответа
    result = await db.execute(
        select(RepairPart)
        .options(selectinload(RepairPart.part))
        .where(RepairPart.id == repair_part.id)
    )

    return RepairPartResponse.from_orm_with_part(
        result.scalar_one()
    )


@router.delete(
    "/{repair_id}/parts/{repair_part_id}",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.MECHANIC))],
)
async def remove_part_from_repair(
        repair_id: int,
        repair_part_id: int,
        db: AsyncSession = Depends(get_db),
):
    await _get_repair_or_404(repair_id, db)

    result = await db.execute(
        select(RepairPart).where(
            RepairPart.id == repair_part_id,
            RepairPart.repair_id == repair_id,
            )
    )

    repair_part = result.scalar_one_or_none()

    if not repair_part:
        raise HTTPException(
            status_code=404,
            detail="Part entry not found in this repair",
        )

    # Возвращаем запчасть на склад
    part = await db.get(Part, repair_part.part_id)

    if part:
        part.quantity += repair_part.quantity

    await db.delete(repair_part)

    await db.commit()

    return {"message": "Part removed from repair, stock restored"}


# ──────────────────────────────────────────────
# Финансовое summary
# ──────────────────────────────────────────────

@router.get(
    "/{repair_id}/summary",
    response_model=RepairFinancialSummary,
)
async def get_repair_summary(
        repair_id: int,
        db: AsyncSession = Depends(get_db),
):
    repair = await _get_repair_or_404(repair_id, db, with_relations=True)

    services_total = sum(
        rs.price for rs in repair.repair_services
    )

    kirill_parts = [
        rp for rp in repair.repair_parts
        if rp.owner == OwnerType.KIRILL
    ]

    vitaly_parts = [
        rp for rp in repair.repair_parts
        if rp.owner == OwnerType.VITALY
    ]

    def _owner_summary(parts: list[RepairPart]) -> OwnerSummary:
        cost = sum(rp.purchase_price * rp.quantity for rp in parts)
        revenue = sum(rp.sale_price * rp.quantity for rp in parts)
        return OwnerSummary(
            parts_cost=round(cost, 2),
            parts_revenue=round(revenue, 2),
            parts_profit=round(revenue - cost, 2),
        )

    parts_total = sum(
        rp.sale_price * rp.quantity for rp in repair.repair_parts
    )

    return RepairFinancialSummary(
        services_total=round(services_total, 2),
        parts_total=round(parts_total, 2),
        total_for_client=round(services_total + parts_total, 2),
        kirill=_owner_summary(kirill_parts),
        vitaly=_owner_summary(vitaly_parts),
    )


# ──────────────────────────────────────────────
# История велосипеда и человека
# ──────────────────────────────────────────────

@router.get(
    "/bikes/{bike_id}/history",
    response_model=list[RepairResponse],
    tags=["History"],
)
async def get_bike_repair_history(
        bike_id: int,
        db: AsyncSession = Depends(get_db),
):
    bike = await db.get(Bike, bike_id)

    if not bike:
        raise HTTPException(
            status_code=404,
            detail="Bike not found",
        )

    result = await db.execute(
        select(Repair)
        .where(Repair.bike_id == bike_id)
        .order_by(Repair.started_at.desc())
    )

    return result.scalars().all()


@router.get(
    "/people/{person_id}/history",
    response_model=list[RepairResponse],
    tags=["History"],
)
async def get_person_repair_history(
        person_id: int,
        db: AsyncSession = Depends(get_db),
):
    person = await db.get(Person, person_id)

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    result = await db.execute(
        select(Repair)
        .where(Repair.client_id == person_id)
        .order_by(Repair.started_at.desc())
    )

    return result.scalars().all()