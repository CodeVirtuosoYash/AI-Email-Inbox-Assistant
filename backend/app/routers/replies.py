from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import RegenerateIn
from app.services.gemini_client import GeminiClientError, regenerate_reply

router = APIRouter()


@router.get("/replies")
def list_replies(db: Session = Depends(get_db)):
    return crud.get_replies(db)


@router.post("/replies/{email_id}/regenerate")
def regenerate(email_id: int, body: RegenerateIn, db: Session = Depends(get_db)):
    """Route param is an email_id, not a Reply's own PK — matches how
    ReplyEditor.jsx always calls this with `emailId`, never a `reply.id`
    (see crud.reply_to_dict, which reports Reply.email_id as "id" for the
    same reason)."""
    email = crud.get_email(db, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        new_reply_text = regenerate_reply(email.subject, email.body, body.tone)
    except GeminiClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    reply = crud.upsert_reply(db, email, new_reply_text, body.tone)
    db.commit()
    return crud.reply_to_dict(reply)
