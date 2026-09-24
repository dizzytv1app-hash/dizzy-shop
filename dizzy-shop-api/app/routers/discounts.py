from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import require_admin
from app.models import Discount
from app.schemas import DiscountIn, DiscountOut

router = APIRouter(tags=["discounts"])


@router.get("/discounts", response_model=list[DiscountOut])
def list_active_discounts(db: Session = Depends(get_db)):
    return db.query(Discount).filter(Discount.active == True).all()  # noqa: E712


@router.get("/admin/discounts")
def admin_list_discounts(db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    items = db.query(Discount).order_by(Discount.created_at.desc()).all()
    return {"items": [DiscountOut.model_validate(d).model_dump() for d in items]}


@router.post("/admin/discounts", response_model=DiscountOut)
def admin_create_discount(data: DiscountIn, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    if not data.product_id and not data.category:
        raise HTTPException(400, "product_id yoki category kerak")
    discount = Discount(percent=data.percent, product_id=data.product_id, category=data.category, active=True)
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


@router.put("/admin/discounts/{discount_id}", response_model=DiscountOut)
def admin_update_discount(discount_id: int, active: bool | None = None, percent: int | None = None, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    discount = db.get(Discount, discount_id)
    if not discount:
        raise HTTPException(404, "Chegirma topilmadi")
    if active is not None:
        discount.active = active
    if percent is not None:
        discount.percent = percent
    db.commit()
    db.refresh(discount)
    return discount


@router.delete("/admin/discounts/{discount_id}")
def admin_delete_discount(discount_id: int, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    discount = db.get(Discount, discount_id)
    if not discount:
        raise HTTPException(404, "Chegirma topilmadi")
    db.delete(discount)
    db.commit()
    return {"ok": True}
