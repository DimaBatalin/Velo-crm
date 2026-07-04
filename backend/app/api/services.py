from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.models.service import Service

from app.schemas.service import ServiceCreate
from app.schemas.service import ServiceUpdate
from app.schemas.service import ServiceResponse


router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=201,
)
async def create_service(
        service_data: ServiceCreate,
        db: AsyncSession = Depends(get_db),
):
    service = Service(**service_data.model_dump())

    db.add(service)

    await db.commit()

    await db.refresh(service)

    return service


@router.get(
    "",
    response_model=list[ServiceResponse],
)
async def get_services(
        search: str | None = None,
        limit: int = Query(default=20, le=200),
        offset: int = 0,
        db: AsyncSession = Depends(get_db),
):
    query = select(Service)

    if search:
        query = query.where(
            Service.name.ilike(f"%{search}%")
        )

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)

    return result.scalars().all()


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
)
async def get_service(
        service_id: int,
        db: AsyncSession = Depends(get_db),
):
    service = await db.get(Service, service_id)

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    return service


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
)
async def update_service(
        service_id: int,
        service_data: ServiceUpdate,
        db: AsyncSession = Depends(get_db),
):
    service = await db.get(Service, service_id)

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    for field, value in service_data.model_dump(exclude_unset=True).items():
        setattr(service, field, value)

    await db.commit()

    await db.refresh(service)

    return service


@router.delete("/{service_id}")
async def delete_service(
        service_id: int,
        db: AsyncSession = Depends(get_db),
):
    service = await db.get(Service, service_id)

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    await db.delete(service)

    await db.commit()

    return {"message": "Service deleted"}