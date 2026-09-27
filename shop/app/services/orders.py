import random
import string
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Order, OrderStatus, OrderSource, Product, User


def _generate_order_number(db: Session) -> str:
    """Takrorlanmas buyurtma raqami. Kollizoyani oldini olish uchun bazadan tekshirib chiqadi."""
    while True:
        number = "ORD-" + "".join(random.choices(string.digits, k=8))
        if not db.query(Order).filter(Order.order_number == number).first():
            return number


def check_selection_available(product: Product, color: str, size: str) -> tuple[bool, str]:
    color_obj = next((c for c in product.colors if c.name == color), None)
    size_obj = next((s for s in product.sizes if s.name == size), None)
    if not color_obj or not color_obj.is_available:
        return False, f"Afsuski, «{color}» rang hozircha mavjud emas."
    if not size_obj or not size_obj.is_available:
        return False, f"Afsuski, «{size}» o'lcham hozircha mavjud emas."
    return True, ""


def create_order(
    db: Session, user: User, product: Product, color: str, size: str, source: OrderSource
) -> tuple[Order | None, str]:
    ok, err = check_selection_available(product, color, size)
    if not ok:
        return None, err

    order = Order(
        order_number=_generate_order_number(db),
        user_id=user.id,
        product_id=product.id,
        product_code=product.code,
        product_name=product.name,
        color=color,
        size=size,
        price=product.price,
        status=OrderStatus.NEW,
        source=source,
    )
    db.add(order)
    db.flush()
    return order, ""


def get_order(db: Session, order_id: int) -> Order | None:
    return db.query(Order).options(joinedload(Order.user), joinedload(Order.product)).filter(
        Order.id == order_id
    ).one_or_none()


def get_order_by_number(db: Session, order_number: str) -> Order | None:
    return db.query(Order).options(joinedload(Order.user), joinedload(Order.product)).filter(
        Order.order_number == order_number
    ).one_or_none()


def list_orders(db: Session, status: OrderStatus | None = None, limit: int = 20) -> list[Order]:
    q = db.query(Order).options(joinedload(Order.user), joinedload(Order.product))
    if status:
        q = q.filter(Order.status == status)
    return q.order_by(Order.created_at.desc()).limit(limit).all()


def accept_order(db: Session, order: Order) -> int:
    """Admin buyurtmani qabul qiladi. 50% oldindan to'lov summasini hisoblab qaytaradi."""
    order.status = OrderStatus.ACCEPTED
    prepay = round(order.price * 0.5)
    order.prepay_amount = prepay
    order.updated_at = datetime.utcnow()
    return prepay


def mark_awaiting_payment(db: Session, order: Order) -> None:
    order.status = OrderStatus.PAYMENT_PENDING


def submit_payment_receipt(db: Session, order: Order, file_id: str) -> None:
    order.payment_receipt_file_id = file_id
    order.status = OrderStatus.PAYMENT_PENDING


def confirm_payment(db: Session, order: Order) -> None:
    order.payment_confirmed = True
    order.status = OrderStatus.PAYMENT_CONFIRMED


def reject_payment(db: Session, order: Order) -> None:
    order.payment_receipt_file_id = None
    order.status = OrderStatus.ACCEPTED  # qayta chek yuborishi uchun


def request_cancel(db: Session, order: Order) -> None:
    order.cancel_requested = True


def admin_cancel_order(db: Session, order: Order) -> None:
    order.status = OrderStatus.CANCELLED
    order.cancel_requested = False


def set_delivery_status(db: Session, order: Order, status: OrderStatus) -> None:
    order.status = status
