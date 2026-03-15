from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import School
from src.schemas import SchoolResponse

router = APIRouter(prefix="/api")


@router.get("/schools", response_model=list[SchoolResponse])
def list_schools(db: Session = Depends(get_db)):
    return db.query(School).order_by(School.name).all()
