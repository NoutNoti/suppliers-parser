from sqlalchemy.orm import Session
from app.dal import category as category_dal

def create_new_category(db: Session, name: str):
    
    return category_dal.create_category_in_db(db=db, name=name)