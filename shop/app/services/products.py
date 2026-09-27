from sqlalchemy.orm import Session, joinedload
from app.models import Product, ProductColor, ProductSize, ProductImage, Order, OrderStatus


def get_product_by_code(db: Session, code: str, active_only: bool = False) -> Product | None:
    q = db.query(Product).options(
        joinedload(Product.colors), joinedload(Product.sizes), joinedload(Product.images)
    ).filter(Product.code == code.strip().upper())
    if active_only:
        q = q.filter(Product.is_active.is_(True))
    return q.one_or_none()


def code_exists(db: Session, code: str) -> bool:
    return db.query(Product).filter(Product.code == code.strip().upper()).first() is not None


def create_product(
    db: Session, code: str, name: str, price: int,
    colors: list[str], sizes: list[str], image_file_ids: list[str],
) -> Product:
    product = Product(code=code.strip().upper(), name=name.strip(), price=price, is_active=True)
    db.add(product)
    db.flush()

    for c in colors:
        db.add(ProductColor(product_id=product.id, name=c.strip(), is_available=True))
    for s in sizes:
        db.add(ProductSize(product_id=product.id, name=s.strip(), is_available=True))
    for i, file_id in enumerate(image_file_ids[:3], start=1):
        db.add(ProductImage(product_id=product.id, file_id=file_id, position=i))

    return product


def list_products(db: Session, active_only: bool = True) -> list[Product]:
    q = db.query(Product)
    if active_only:
        q = q.filter(Product.is_active.is_(True))
    return q.order_by(Product.created_at.desc()).all()


def update_field(db: Session, product: Product, field: str, value) -> None:
    setattr(product, field, value)


def set_color_availability(db: Session, product: Product, color_name: str, available: bool) -> bool:
    color = next((c for c in product.colors if c.name.lower() == color_name.lower()), None)
    if not color:
        return False
    color.is_available = available
    return True


def set_size_availability(db: Session, product: Product, size_name: str, available: bool) -> bool:
    size = next((s for s in product.sizes if s.name.lower() == size_name.lower()), None)
    if not size:
        return False
    size.is_available = available
    return True


def replace_images(db: Session, product: Product, image_file_ids: list[str]) -> None:
    for img in list(product.images):
        db.delete(img)
    db.flush()
    for i, file_id in enumerate(image_file_ids[:3], start=1):
        db.add(ProductImage(product_id=product.id, file_id=file_id, position=i))


def delete_product(db: Session, product: Product) -> None:
    # Tarixiy buyurtmalar buzilmasligi uchun "soft delete" - is_active=False qilamiz
    product.is_active = False


def set_discount(db: Session, product: Product, new_price: int) -> float:
    """Yangi (chegirmali) narxni qo'yadi va foizni hisoblab qaytaradi."""
    old_price = product.price
    percent = round((old_price - new_price) / old_price * 100, 1)
    product.old_price = old_price
    product.price = new_price
    product.discount_percent = percent
    return percent


def remove_discount(db: Session, product: Product) -> None:
    product.old_price = None
    product.discount_percent = None


def sold_count(db: Session, product_id: int) -> int:
    return (
        db.query(Order)
        .filter(Order.product_id == product_id, Order.status != OrderStatus.CANCELLED,
                Order.payment_confirmed.is_(True))
        .count()
    )
