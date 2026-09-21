from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db

router = APIRouter()


@router.get("/messages")
def list_messages(db: Session = Depends(get_db)):
    """Every analyzed email, any category — Messages.jsx filters client-side."""
    return crud.get_analyses(db)
