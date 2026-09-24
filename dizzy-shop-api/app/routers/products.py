from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.auth import require_admin
from app.models import Product, Discount
from app.schemas import ProductIn, ProductUpdate, ProductOut
from app.classify import classify_product

router = APIRouter(tags=["products"])


def _with_discount(db: Session, product: Product) -> ProductOut:
    out = ProductOut.model_validate(product)
    disc = (
        db.query(Discount)
        .filter(Discount.active == True)  # noqa: E712
        .filter(or_(Discount.product_id == product.id, Discount.category == product.category))
        .order_by(Discount.percent.desc())
        .first()
    )
    out.discount_percent = disc.percent if disc else 0
    return out


# ---------- Ommaviy (mini app) ----------

@router.get("/products", response_model=list[ProductOut])
def list_products(
    category: str | None = None,
    search: str | None = None,
    section: str | None = Query(default=None, description="new | popular | discount"),
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category == category)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if section == "new":
        q = q.order_by(Product.created_at.desc()).limit(12)
    elif section == "popular":
        q = q.order_by(Product.id.desc()).limit(12)  # demo: haqiqiy loyihada sotuv soni bo'yicha
    else:
        q = q.order_by(Product.created_at.desc())

    products = q.all()
    result = [_with_discount(db, p) for p in products]
    if section == "discount":
        result = [p for p in result if p.discount_percent > 0]
    return result


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    return _with_discount(db, product)


# ---------- Admin (bot orqali) ----------

@router.post("/admin/products", response_model=ProductOut)
def admin_create_product(data: ProductIn, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    product = Product(
        name=data.name,
        price=data.price,
        sizes=data.sizes,
        colors=data.colors,
        stock=data.stock,
        image_file_id=data.image_file_id,
        category=classify_product(data.name),
        is_new=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _with_discount(db, product)


@router.get("/admin/products")
def admin_list_products(
    page: int = 0,
    limit: int = 8,
    search: str | None = None,
    db: Session = Depends(get_db),
    _admin: int = Depends(require_admin),
):
    q = db.query(Product).order_by(Product.created_at.desc())
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    total = q.count()
    items = q.offset(page * limit).limit(limit).all()
    return {
        "items": [ProductOut.model_validate(p).model_dump() for p in items],
        "has_next": (page + 1) * limit < total,
    }


@router.put("/admin/products/{product_id}", response_model=ProductOut)
def admin_update_product(
    product_id: int, data: ProductUpdate, db: Session = Depends(get_db), _admin: int = Depends(require_admin)
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)
    if "name" in updates:
        product.category = classify_product(product.name)

    db.commit()
    db.refresh(product)
    return _with_discount(db, product)


@router.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: int, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    db.delete(product)
    db.commit()
    return {"ok": True}
