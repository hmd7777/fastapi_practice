from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .session import SessionLocal
from .models import Iris
from .schemas import IrisOut

router = APIRouter()

# dependency to get a db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/data", response_model=list[IrisOut])
def get_chart_data(db: Session = Depends(get_db)):
    flowers = db.query(Iris).all()
    return flowers

