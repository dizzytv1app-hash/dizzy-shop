from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import require_admin
from app.models import HelpRequest
from app.schemas import HelpRequestIn, HelpStatusUpdate

router = APIRouter(tags=["help"])

VALID_STATUSES = {"new", "in_progress", "resolved"}


@router.post("/support")
def create_support_ticket(data: HelpRequestIn, db: Session = Depends(get_db)):
    """Bot /help buyrug'ida chaqiradi (admin auth talab qilinmaydi — foydalanuvchi yozayapti)."""
    ticket = HelpRequest(
        user_id=data.user_id, username=data.username, message=data.message,
        photo_file_id=data.photo_file_id, status="new",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return {"id": ticket.id}


@router.get("/admin/support")
def admin_list_support(status: str | None = None, page: int = 0, limit: int = 8, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    q = db.query(HelpRequest).order_by(HelpRequest.created_at.desc())
    if status:
        q = q.filter(HelpRequest.status == status)
    total = q.count()
    items = q.offset(page * limit).limit(limit).all()
    return {
        "items": [
            {
                "id": t.id, "user_id": t.user_id, "username": t.username, "message": t.message,
                "photo_file_id": t.photo_file_id, "status": t.status,
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for t in items
        ],
        "has_next": (page + 1) * limit < total,
    }


@router.post("/admin/support/{ticket_id}/reply")
def admin_reply_support(ticket_id: int, data: HelpStatusUpdate, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    ticket = db.get(HelpRequest, ticket_id)
    if not ticket:
        raise HTTPException(404, "So'rov topilmadi")
    if data.reply:
        ticket.admin_reply = data.reply
        ticket.status = "resolved"
    if data.status:
        if data.status not in VALID_STATUSES:
            raise HTTPException(400, "Noto'g'ri status")
        ticket.status = data.status
    db.commit()
    return {"ok": True, "user_id": ticket.user_id}
