from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.database import get_db
from app.auth import get_current_user, require_admin
from app.models import Order, OrderItem, Cart, CartItem, Product, Discount
from app.schemas import OrderOut, OrderStatusUpdate
from app.routers.users import upsert_user
from app.routers.cart import _get_or_create_cart
from app.telegram_notify import notify_admins

router = APIRouter(tags=["orders"])

STATUS_LABELS = {"new": "🆕 Yangi", "processing": "⏳ Jarayonda", "completed": "✅ Bajarildi", "cancelled": "🚫 Bekor qilindi"}


def _active_discount(db: Session, product: Product) -> int:
    disc = (
        db.query(Discount)
        .filter(Discount.active == True)  # noqa: E712
        .filter((Discount.product_id == product.id) | (Discount.category == product.category))
        .order_by(Discount.percent.desc())
        .first()
    )
    return disc.percent if disc else 0


@router.post("/orders", response_model=OrderOut)
def checkout(db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user), background: BackgroundTasks = None):
    user = upsert_user(db, tg_user)
    cart = _get_or_create_cart(db, user.id)
    if not cart.items:
        raise HTTPException(400, "Savat bo'sh")

    order = Order(user_id=user.id, total_price=0, status="new")
    db.add(order)
    db.flush()

    total = 0
    lines = []
    for ci in cart.items:
        product = ci.product
        if not product or product.stock < ci.quantity:
            raise HTTPException(400, f"'{product.name if product else '???'}' yetarli emas")
        discount = _active_discount(db, product)
        unit_price = float(product.price) * (1 - discount / 100)
        line_total = unit_price * ci.quantity

        db.add(OrderItem(
            order_id=order.id, product_id=product.id, product_name=product.name,
            size=ci.size, color=ci.color, quantity=ci.quantity, price=unit_price,
        ))
        product.stock -= ci.quantity
        total += line_total
        lines.append(f"- {product.name} x{ci.quantity}")

    order.total_price = total
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(order)

    customer = f"@{user.username}" if user.username else user.first_name or f"id{user.id}"
    text = (
        f"🛒 Yangi buyurtma\n\n"
        f"Buyurtma ID: #{order.id}\n"
        f"Mijoz: {customer}\n"
        f"Umumiy: {int(total)} so'm\n\n"
        f"Mahsulotlar:\n" + "\n".join(lines)
    )
    if background is not None:
        background.add_task(notify_admins, text)

    return _order_out(order)


def _order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        total_price=float(order.total_price),
        status=order.status,
        created_at=order.created_at,
        items=[
            {"product_name": i.product_name, "size": i.size, "color": i.color, "quantity": i.quantity, "price": float(i.price)}
            for i in order.items
        ],
    )


@router.get("/orders", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), tg_user: dict = Depends(get_current_user)):
    user = upsert_user(db, tg_user)
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return [_order_out(o) for o in orders]


# ---------- Admin ----------

@router.get("/admin/orders")
def admin_list_orders(page: int = 0, limit: int = 8, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    q = db.query(Order).order_by(Order.created_at.desc())
    total = q.count()
    orders = q.offset(page * limit).limit(limit).all()
    items = []
    for o in orders:
        user = o.user
        customer = f"@{user.username}" if user and user.username else (user.first_name if user else "Mehmon")
        items.append({
            "id": o.id, "customer": customer, "total_price": float(o.total_price),
            "status": o.status, "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    return {"items": items, "has_next": (page + 1) * limit < total}


@router.put("/admin/orders/{order_id}/status")
def admin_set_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    if data.status not in STATUS_LABELS:
        raise HTTPException(400, "Noto'g'ri status")
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    order.status = data.status
    db.commit()
    return {"ok": True, "user_id": order.user_id, "status": order.status}
