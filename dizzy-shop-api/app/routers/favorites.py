from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import get_current_user
from app.models import Favorite, Product
from app.schemas import FavoriteToggle, ProductOut
from app.routers.users import upsert_user
from app.routers.products import _with_discount

router = APIRouter(tags=["favorites"])


@router.get("/favorites", response_model=list[ProductOut])
def list_favorites(db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    favs = db.query(Favorite).filter(Favorite.user_id == user.id).all()
    return [_with_discount(db, f.product) for f in favs if f.product]


@router.post("/favorites")
def add_favorite(data: FavoriteToggle, db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    if not db.get(Product, data.product_id):
        raise HTTPException(404, "Mahsulot topilmadi")
    exists = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id, Favorite.product_id == data.product_id)
        .first()
    )
    if not exists:
        db.add(Favorite(user_id=user.id, product_id=data.product_id))
        db.commit()
    return {"ok": True}


@router.delete("/favorites/{product_id}")
def remove_favorite(product_id: int, db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.product_id == product_id).delete()
    db.commit()
    return {"ok": True}
