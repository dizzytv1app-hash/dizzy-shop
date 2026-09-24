from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from app.config import settings

# Faqat chegirma maqsadida ishlatiladi (admin mahsulot qo'shganda kategoriya so'ralmaydi)
CATEGORIES = [
    ("clothing", "👕 Kiyim"),
    ("anime", "🎌 Anime"),
    ("gaming", "🎮 Gaming"),
    ("streetwear", "🖤 Streetwear"),
    ("shoes", "👟 Poyabzal"),
    ("accessories", "🧢 Aksessuar"),
]


def open_shop_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛍️ Do'konni ochish", web_app=WebAppInfo(url=settings.WEBAPP_URL))]],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
            [InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="adm:add_product")],
            [InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="adm:products:0")],
            [InlineKeyboardButton(text="🛒 Buyurtmalar", callback_data="adm:orders:0")],
            [InlineKeyboardButton(text="💬 Yordam so'rovlari", callback_data="adm:support:0")],
            [InlineKeyboardButton(text="🏷️ Chegirmalar", callback_data="adm:discounts")],
            [InlineKeyboardButton(text="📢 Ilova ma'lumoti", callback_data="adm:content")],
            [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="adm:settings")],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:menu")]])


def confirm_cancel_keyboard(confirm_cb: str, cancel_cb: str = "adm:cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Saqlash", callback_data=confirm_cb),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=cancel_cb),
        ]]
    )


def product_row_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✏️ Nomi", callback_data=f"adm:editf:{product_id}:name"),
            InlineKeyboardButton(text="💵 Narxi", callback_data=f"adm:editf:{product_id}:price"),
        ], [
            InlineKeyboardButton(text="📏 O'lcham", callback_data=f"adm:editf:{product_id}:sizes"),
            InlineKeyboardButton(text="🎨 Rang", callback_data=f"adm:editf:{product_id}:colors"),
        ], [
            InlineKeyboardButton(text="📦 Qoldiq", callback_data=f"adm:editf:{product_id}:stock"),
            InlineKeyboardButton(text="🖼 Rasm", callback_data=f"adm:editf:{product_id}:photo"),
        ], [
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm:delete:{product_id}"),
        ]]
    )


def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    statuses = [("new", "🆕 Yangi"), ("processing", "⏳ Jarayonda"), ("completed", "✅ Bajarildi"), ("cancelled", "🚫 Bekor qilindi")]
    rows = [[InlineKeyboardButton(text=label, callback_data=f"adm:order_status:{order_id}:{code}")] for code, label in statuses]
    rows.append([InlineKeyboardButton(text="⬅️ Buyurtmalar", callback_data="adm:orders:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_status_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Jarayonda", callback_data=f"adm:help_status:{ticket_id}:in_progress"),
                InlineKeyboardButton(text="✅ Hal qilindi", callback_data=f"adm:help_status:{ticket_id}:resolved"),
            ],
            [InlineKeyboardButton(text="✍️ Javob yozish", callback_data=f"adm:reply:{ticket_id}")],
            [InlineKeyboardButton(text="⬅️ Yordam so'rovlari", callback_data="adm:support:0")],
        ]
    )


def discount_target_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📁 Kategoriyaga", callback_data="disc_target:category")],
            [InlineKeyboardButton(text="🔢 Mahsulot ID orqali", callback_data="disc_target:product")],
        ]
    )


def category_pick_keyboard(prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"{prefix}:{slug}")] for slug, label in CATEGORIES]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Birinchi ochilish matni", callback_data="adm:content_edit:onboarding")],
            [InlineKeyboardButton(text="📖 Qo'llanma matni", callback_data="adm:content_edit:guide")],
            [InlineKeyboardButton(text="🏬 Do'kon haqida", callback_data="adm:content_edit:shop_info")],
            [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:menu")],
        ]
    )


def pagination_keyboard(prefix: str, page: int, has_next: bool) -> InlineKeyboardMarkup:
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{page - 1}"))
    if has_next:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page + 1}"))
    rows = [row] if row else []
    rows.append([InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
