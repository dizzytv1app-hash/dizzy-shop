from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.auth import get_current_user
from app.models import Cart, CartItem, Product
from app.schemas import CartItemIn, CartItemUpdate, CartItemOut
from app.routers.users import upsert_user
from app.routers.products import _with_discount

router = APIRouter(tags=["cart"])


def _get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("/cart", response_model=list[CartItemOut])
def get_cart(db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    cart = _get_or_create_cart(db, user.id)
    return [
        CartItemOut(id=i.id, product=_with_discount(db, i.product), size=i.size, color=i.color, quantity=i.quantity)
        for i in cart.items
        if i.product
    ]


@router.post("/cart")
def add_to_cart(data: CartItemIn, db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    cart = _get_or_create_cart(db, user.id)

    existing = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == data.product_id,
            CartItem.size == data.size,
            CartItem.color == data.color,
        )
        .first()
    )
    if existing:
        existing.quantity += data.quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=data.product_id, size=data.size, color=data.color, quantity=data.quantity))
    db.commit()
    return {"ok": True}


@router.put("/cart/{item_id}")
def update_cart_item(item_id: int, data: CartItemUpdate, db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    cart = _get_or_create_cart(db, user.id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(404, "Element topilmadi")
    if data.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = data.quantity
    db.commit()
    return {"ok": True}


@router.delete("/cart/{item_id}")
def remove_cart_item(item_id: int, db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    cart = _get_or_create_cart(db, user.id)
    db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"ok": True}
