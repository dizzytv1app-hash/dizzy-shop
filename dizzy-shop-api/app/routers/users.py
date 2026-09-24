from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_db
from app.auth import get_current_user
from app.models import User

router = APIRouter(tags=["users"])


def upsert_user(db: Session, tg_user: dict) -> User:
    user = db.get(User, tg_user["id"])
    if user is None:
        user = User(id=tg_user["id"], username=tg_user.get("username"), first_name=tg_user.get("first_name"))
        db.add(user)
    else:
        user.username = tg_user.get("username") or user.username
        user.first_name = tg_user.get("first_name") or user.first_name
    db.commit()
    db.refresh(user)
    return user


@router.get("/me")
def get_me(db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    return {"id": user.id, "username": user.username, "first_name": user.first_name}
