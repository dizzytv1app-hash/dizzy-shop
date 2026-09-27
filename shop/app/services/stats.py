from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User, Product, Order, OrderStatus


def _today_range():
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _month_start():
    now = datetime.utcnow()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_full_stats(db: Session) -> dict:
    today_start, today_end = _today_range()
    month_start = _month_start()

    total_users = db.query(func.count(User.id)).scalar() or 0
    new_users_today = (
        db.query(func.count(User.id))
        .filter(User.created_at >= today_start, User.created_at < today_end)
        .scalar() or 0
    )
    total_products = db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0

    pending_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status.in_([OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.PAYMENT_PENDING]))
        .scalar() or 0
    )
    confirmed_orders = (
        db.query(func.count(Order.id)).filter(Order.status == OrderStatus.PAYMENT_CONFIRMED).scalar() or 0
    )
    delivered_orders = (
        db.query(func.count(Order.id)).filter(Order.status == OrderStatus.DELIVERED).scalar() or 0
    )
    cancelled_orders = (
        db.query(func.count(Order.id)).filter(Order.status == OrderStatus.CANCELLED).scalar() or 0
    )

    # Haqiqiy savdo = faqat to'lovi tasdiqlangan va bekor qilinmagan buyurtmalar
    real_sale_filter = [Order.payment_confirmed.is_(True), Order.status != OrderStatus.CANCELLED]

    today_sales = (
        db.query(func.coalesce(func.sum(Order.price), 0))
        .filter(*real_sale_filter, Order.updated_at >= today_start, Order.updated_at < today_end)
        .scalar() or 0
    )
    month_sales = (
        db.query(func.coalesce(func.sum(Order.price), 0))
        .filter(*real_sale_filter, Order.updated_at >= month_start)
        .scalar() or 0
    )
    total_sales = (
        db.query(func.coalesce(func.sum(Order.price), 0)).filter(*real_sale_filter).scalar() or 0
    )

    top_products = (
        db.query(Order.product_name, Order.product_code, func.count(Order.id).label("cnt"))
        .filter(*real_sale_filter)
        .group_by(Order.product_code, Order.product_name)
        .order_by(func.count(Order.id).desc())
        .limit(10)
        .all()
    )

    top_customers = (
        db.query(User.full_name, User.username, User.telegram_id, func.count(Order.id).label("cnt"))
        .join(Order, Order.user_id == User.id)
        .filter(*real_sale_filter)
        .group_by(User.id)
        .order_by(func.count(Order.id).desc())
        .limit(10)
        .all()
    )

    return {
        "total_users": total_users,
        "new_users_today": new_users_today,
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "today_sales": today_sales,
        "month_sales": month_sales,
        "total_sales": total_sales,
        "top_products": top_products,
        "top_customers": top_customers,
    }
