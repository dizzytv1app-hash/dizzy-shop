"""
Ma'lumotlar bazasi modellari.
Bitta baza - bot va (kelajakdagi) web-sayt API'si shu modellardan foydalanadi.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, Float, DateTime,
    ForeignKey, Text, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    NEW = "NEW"                          # Yangi
    ACCEPTED = "ACCEPTED"                # Qabul qilindi
    PAYMENT_PENDING = "PAYMENT_PENDING"  # To'lov kutilmoqda (chek yuborilgan yoki hali yuborilmagan)
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"  # To'lov tasdiqlandi
    DELIVERING = "DELIVERING"            # Yetkazib berilmoqda
    DELIVERED = "DELIVERED"              # Yetkazildi
    CANCELLED = "CANCELLED"              # Bekor qilindi

    @classmethod
    def label(cls, status: "OrderStatus") -> str:
        return {
            cls.NEW: "🆕 Yangi",
            cls.ACCEPTED: "✅ Qabul qilindi",
            cls.PAYMENT_PENDING: "⏳ To'lov kutilmoqda",
            cls.PAYMENT_CONFIRMED: "💰 To'lov tasdiqlandi",
            cls.DELIVERING: "🚚 Yetkazib berilmoqda",
            cls.DELIVERED: "📦 Yetkazildi",
            cls.CANCELLED: "❌ Bekor qilindi",
        }[status]


class OrderSource(str, enum.Enum):
    BOT = "BOT"
    WEBSITE = "WEBSITE"
    CHANNEL = "CHANNEL"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user")
    help_requests = relationship("HelpRequest", back_populates="user")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    is_owner = Column(Boolean, default=False)
    added_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)  # masalan K001
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)          # hozirgi (yakuniy) narx, so'mda
    old_price = Column(Integer, nullable=True)       # chegirmadan oldingi narx (bo'lsa)
    discount_percent = Column(Float, nullable=True)  # avtomatik hisoblangan foiz
    is_active = Column(Boolean, default=True)        # o'chirilgan mahsulotlar is_active=False
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    colors = relationship("ProductColor", back_populates="product", cascade="all, delete-orphan")
    sizes = relationship("ProductSize", back_populates="product", cascade="all, delete-orphan")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan",
                           order_by="ProductImage.position")
    orders = relationship("Order", back_populates="product")

    @property
    def has_discount(self) -> bool:
        return self.old_price is not None and self.old_price > self.price


class ProductColor(Base):
    __tablename__ = "product_colors"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_product_color"),)

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)

    product = relationship("Product", back_populates="colors")


class ProductSize(Base):
    __tablename__ = "product_sizes"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_product_size"),)

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)

    product = relationship("Product", back_populates="sizes")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    file_id = Column(String, nullable=False)   # Telegram file_id (rasm Telegram serverida saqlanadi)
    position = Column(Integer, default=1)      # 1=old, 2=orqa, 3=qo'shimcha

    product = relationship("Product", back_populates="images")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product_code = Column(String, nullable=False)   # buyurtma vaqtidagi holatni saqlash uchun
    product_name = Column(String, nullable=False)
    color = Column(String, nullable=False)
    size = Column(String, nullable=False)
    price = Column(Integer, nullable=False)          # buyurtma berilgan paytdagi narx
    prepay_amount = Column(Integer, nullable=True)    # 50% oldindan to'lov

    status = Column(SAEnum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    source = Column(SAEnum(OrderSource), default=OrderSource.BOT, nullable=False)

    payment_receipt_file_id = Column(String, nullable=True)  # mijoz yuborgan chek rasmi
    payment_confirmed = Column(Boolean, default=False)       # faqat admin tasdiqlasa True
    cancel_requested = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")


class HelpRequest(Base):
    __tablename__ = "help_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=True)
    photo_file_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    forwarded = Column(Boolean, default=False)

    user = relationship("User", back_populates="help_requests")


class Setting(Base):
    """Help chat ID, kanal ID, karta raqami kabi o'zgaruvchan sozlamalar shu yerda saqlanadi."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
