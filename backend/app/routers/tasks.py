from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import TaskPatchIn

router = APIRouter()


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return crud.get_tasks(db)


@router.patch("/tasks/{task_id}")
def patch_task(task_id: int, body: TaskPatchIn, db: Session = Depends(get_db)):
    task = crud.update_task_status(db, task_id, body.status)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.commit()
    return crud.task_to_dict(task)
