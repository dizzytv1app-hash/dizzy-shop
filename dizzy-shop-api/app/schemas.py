from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ---------- Products ----------

class ProductIn(BaseModel):
    name: str
    price: float
    sizes: list[str] = []
    colors: list[str] = []
    stock: int = 0
    image_file_id: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    sizes: list[str] | None = None
    colors: list[str] | None = None
    stock: int | None = None
    image_file_id: str | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    price: float
    sizes: list[str]
    colors: list[str]
    stock: int
    image_file_id: str | None
    category: str
    is_new: bool
    discount_percent: int = 0


# ---------- Favorites / Cart ----------

class FavoriteToggle(BaseModel):
    product_id: int


class CartItemIn(BaseModel):
    product_id: int
    size: str | None = None
    color: str | None = None
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    size: str | None
    color: str | None
    quantity: int


# ---------- Orders ----------

class OrderCreate(BaseModel):
    pass  # savatdagi mavjud narsalardan avtomatik yaratiladi


class OrderItemOut(BaseModel):
    product_name: str
    size: str | None
    color: str | None
    quantity: int
    price: float


class OrderOut(BaseModel):
    id: int
    total_price: float
    status: str
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: str


# ---------- Help requests ----------

class HelpRequestIn(BaseModel):
    user_id: int
    username: str | None = None
    message: str
    photo_file_id: str | None = None


class HelpRequestOut(BaseModel):
    id: int
    user_id: int
    username: str | None
    message: str
    photo_file_id: str | None
    status: str
    admin_reply: str | None
    created_at: datetime


class HelpStatusUpdate(BaseModel):
    status: str | None = None
    reply: str | None = None


# ---------- Discounts ----------

class DiscountIn(BaseModel):
    percent: int
    product_id: int | None = None
    category: str | None = None


class DiscountOut(BaseModel):
    id: int
    percent: int
    product_id: int | None
    category: str | None
    active: bool


# ---------- Content (onboarding / guide / shop info) ----------

class ContentOut(BaseModel):
    key: str
    value: str


class ContentUpdate(BaseModel):
    value: str


# ---------- Stats ----------

class BestSeller(BaseModel):
    name: str
    sold: int


class LowStock(BaseModel):
    name: str
    stock: int


class StatsOut(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_sales: float
    today_orders: int
    today_sales: float
    weekly_sales: float
    monthly_sales: float
    total_help_requests: int
    new_help_requests: int
    best_sellers: list[BestSeller]
    low_stock: list[LowStock]
