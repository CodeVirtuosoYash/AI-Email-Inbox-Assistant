from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.agent import summarize as run_summarize

router = APIRouter()


@router.post("/summarize")
def post_summarize(db: Session = Depends(get_db)):
    rollup, failures = run_summarize(db)
    if failures:
        # additive/non-breaking: surfaced for debugging, frontend ignores unknown keys
        rollup["failed_batches"] = [{"source_ids": f.source_ids, "error": f.error} for f in failures]
    return rollup
