from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import School
from src.schemas import SchoolResponse

router = APIRouter(prefix="/api")


@router.get("/schools", response_model=list[SchoolResponse])
async def list_schools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).order_by(School.name))
    return result.scalars().all()
