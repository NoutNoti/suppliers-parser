from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services import category as category_service

router = APIRouter()

@router.post("/")
def add_category(name: str, db: Session = Depends(get_db)):
    # Передаємо запит у шар Services
    return category_service.create_new_category(db=db, name=name)