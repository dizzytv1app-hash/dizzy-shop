from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_db
from app.auth import require_admin
from app.models import User, Product, Order, OrderItem, HelpRequest

router = APIRouter(tags=["stats"])


@router.get("/admin/stats")
def get_stats(db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_sales = db.query(func.coalesce(func.sum(Order.total_price), 0)).scalar() or 0

    today_orders = db.query(func.count(Order.id)).filter(Order.created_at >= today_start).scalar() or 0
    today_sales = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(Order.created_at >= today_start).scalar() or 0
    weekly_sales = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(Order.created_at >= week_start).scalar() or 0
    monthly_sales = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(Order.created_at >= month_start).scalar() or 0

    total_help = db.query(func.count(HelpRequest.id)).scalar() or 0
    new_help = db.query(func.count(HelpRequest.id)).filter(HelpRequest.status == "new").scalar() or 0

    best_rows = (
        db.query(OrderItem.product_name, func.coalesce(func.sum(OrderItem.quantity), 0).label("sold"))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    low_rows = (
        db.query(Product.name, Product.stock)
        .filter(Product.stock <= 3)
        .order_by(Product.stock.asc())
        .limit(5)
        .all()
    )

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_sales": float(total_sales),
        "today_orders": today_orders,
        "today_sales": float(today_sales),
        "weekly_sales": float(weekly_sales),
        "monthly_sales": float(monthly_sales),
        "total_help_requests": total_help,
        "new_help_requests": new_help,
        "best_sellers": [{"name": n, "sold": int(s)} for n, s in best_rows],
        "low_stock": [{"name": n, "stock": s} for n, s in low_rows],
    }
