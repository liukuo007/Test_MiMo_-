from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("")
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query("", description="按名称搜索"),
    dataset_type: str = Query("", description="按类型筛选"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Dataset).order_by(Dataset.created_at.desc())
    count_query = select(func.count(Dataset.id))

    if search:
        query = query.where(Dataset.name.ilike(f"%{search}%"))
        count_query = count_query.where(Dataset.name.ilike(f"%{search}%"))
    if dataset_type:
        query = query.where(Dataset.type == dataset_type)
        count_query = count_query.where(Dataset.type == dataset_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()

    return {
        "items": [DatasetResponse.model_validate(d).model_dump() for d in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("")
async def create_dataset(
    data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = Dataset(**data.model_dump(), created_by=current_user.id)
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)
    return DatasetResponse.model_validate(dataset).model_dump()


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"数据集 {dataset_id} 不存在")
    return DatasetResponse.model_validate(dataset).model_dump()


@router.put("/{dataset_id}")
async def update_dataset(
    dataset_id: int,
    data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"数据集 {dataset_id} 不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dataset, field, value)

    await db.flush()
    await db.refresh(dataset)
    return DatasetResponse.model_validate(dataset).model_dump()


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"数据集 {dataset_id} 不存在")

    await db.delete(dataset)
    return {"message": "deleted", "id": dataset_id}
