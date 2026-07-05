from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.models.tag import Tag

from app.schemas.tag import TagCreate
from app.schemas.tag import TagResponse


router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


@router.get(
    "",
    response_model=list[TagResponse],
)
async def get_tags(
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


@router.post(
    "",
    response_model=TagResponse,
    status_code=201,
)
async def create_tag(
        tag_data: TagCreate,
        db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Tag).where(Tag.name == tag_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Tag with this name already exists",
        )

    tag = Tag(name=tag_data.name)

    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    return tag
