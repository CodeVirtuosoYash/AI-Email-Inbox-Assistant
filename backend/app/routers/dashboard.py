from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.rollup import build_rollup

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Before the first Summarize run this returns the empty-state shape
    (last_summarized_at=None, empty lists, zeroed counts) — the Dashboard
    page already renders that as "no info yet" without special-casing."""
    return build_rollup(db)
