from sqlalchemy.orm import Session
from app.models.category import Category

def create_category_in_db(db: Session, name: str):
    
    db_category = Category(name=name)
    
    db.add(db_category)
    
    db.commit()
    
    db.refresh(db_category)
    
    return db_category