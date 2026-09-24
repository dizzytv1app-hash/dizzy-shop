from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # Telegram user id
    username = Column(String(64), nullable=True)
    first_name = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    sizes = Column(JSON, default=list)          # ["S", "M", "L"]
    colors = Column(JSON, default=list)         # ["Qora", "Oq"]
    stock = Column(Integer, default=0)
    image_file_id = Column(String(255), nullable=True)  # Telegram file_id
    category = Column(String(32), default="clothing")   # avtomatik aniqlanadi, admin tanlamaydi
    is_new = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    product = relationship("Product")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size = Column(String(16), nullable=True)
    color = Column(String(32), nullable=True)
    quantity = Column(Integer, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    status = Column(String(16), default="new")  # new, processing, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200))  # narx/nom o'zgarsa ham buyurtmada saqlanadi
    size = Column(String(16), nullable=True)
    color = Column(String(32), nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(Numeric(12, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


class HelpRequest(Base):
    __tablename__ = "help_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    photo_file_id = Column(String(255), nullable=True)
    status = Column(String(16), default="new")  # new, in_progress, resolved
    admin_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True)
    percent = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    category = Column(String(32), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Content(Base):
    """Admin bot orqali tahrirlaydigan matnlar: birinchi ochilish, qo'llanma, do'kon haqida."""
    __tablename__ = "content"

    key = Column(String(32), primary_key=True)  # onboarding | guide | shop_info
    value = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
