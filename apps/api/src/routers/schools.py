from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import School
from src.schemas import SchoolResponse

router = APIRouter(prefix="/api")


@router.get("/schools", response_model=list[SchoolResponse])
async def list_schools(
    gender: str | None = Query(None, description="Filter by gender: 'men' or 'women'"),
    conference: str | None = Query(None, description="Filter by conference abbreviation e.g. 'GAC'"),
    db: AsyncSession = Depends(get_db),
) -> list[School]:
    stmt = select(School).where(School.enabled == True)
    if gender:
        stmt = stmt.where(School.gender == gender)
    if conference:
        stmt = stmt.where(School.conference == conference)
    result = await db.execute(stmt.order_by(School.name))
    return result.scalars().all()
