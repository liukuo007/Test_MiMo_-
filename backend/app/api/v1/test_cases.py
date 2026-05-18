from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.test_case import TestCase, TestType, Priority
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from app.dependencies import CurrentUser
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("")
async def list_test_cases(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
    project_id: Optional[int] = None,
    test_type: Optional[TestType] = None,
    priority: Optional[Priority] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(TestCase)
    count_query = select(func.count(TestCase.id))
    if project_id:
        query = query.where(TestCase.project_id == project_id)
        count_query = count_query.where(TestCase.project_id == project_id)
    if test_type:
        query = query.where(TestCase.test_type == test_type)
        count_query = count_query.where(TestCase.test_type == test_type)
    if priority:
        query = query.where(TestCase.priority == priority)
        count_query = count_query.where(TestCase.priority == priority)
    if search:
        search_filter = TestCase.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(TestCase.id.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=TestCaseResponse)
async def create_test_case(req: TestCaseCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    test_case = TestCase(
        **req.model_dump(),
        created_by=int(current_user["sub"]),
    )
    db.add(test_case)
    await db.flush()
    await db.refresh(test_case)
    return test_case


@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_test_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise NotFoundError("TestCase", case_id)
    return test_case


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case(case_id: int, req: TestCaseUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise NotFoundError("TestCase", case_id)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(test_case, field, value)

    await db.flush()
    await db.refresh(test_case)
    return test_case


@router.delete("/{case_id}")
async def delete_test_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise NotFoundError("TestCase", case_id)

    await db.delete(test_case)
    await db.flush()
    return {"message": f"TestCase {case_id} deleted"}
