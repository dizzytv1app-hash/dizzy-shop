from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
)
from app.config import settings

# ---------- Foydalanuvchi uchun ----------

def main_user_keyboard() -> ReplyKeyboardMarkup | None:
    if not settings.WEBSITE_URL:
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛍 Do'kon saytiga o'tish", web_app=WebAppInfo(url=settings.WEBSITE_URL))]],
        resize_keyboard=True,
    )


# ---------- Admin asosiy menyusi ----------

ADMIN_MENU_BUTTONS = [
    "➕ Kiyim qo'shish",
    "🛠 Kiyimlarni boshqarish",
    "📊 Kiyimlarni tahlillash",
    "📦 Buyurtmalar",
    "🏷 Chegirmalar",
    "📈 Statistika",
    "👤 Adminlar",
    "💬 Help chatini ulash",
    "📤 Kanalga yuborish",
    "💳 Karta sozlash",
    "⬅️ Chiqish",
]


def admin_main_menu() -> ReplyKeyboardMarkup:
    rows = [ADMIN_MENU_BUTTONS[i:i + 2] for i in range(0, len(ADMIN_MENU_BUTTONS), 2)]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in rows],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🚫 Bekor qilish")]], resize_keyboard=True)


def finish_or_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Tugatish")], [KeyboardButton(text="🚫 Bekor qilish")]],
        resize_keyboard=True,
    )


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➡️ O'tkazib yuborish")], [KeyboardButton(text="🚫 Bekor qilish")]],
        resize_keyboard=True,
    )


def confirm_delete_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"delprod_yes:{code}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="delprod_no"),
    ]])


def manage_product_menu(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Nomi", callback_data=f"editname:{code}"),
         InlineKeyboardButton(text="💵 Narxi", callback_data=f"editprice:{code}")],
        [InlineKeyboardButton(text="🎨 Ranglar", callback_data=f"editcolors:{code}"),
         InlineKeyboardButton(text="📏 O'lchamlar", callback_data=f"editsizes:{code}")],
        [InlineKeyboardButton(text="🖼 Rasmlar", callback_data=f"editimages:{code}")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delprod:{code}")],
    ])


def color_manage_keyboard(code: str, colors: list) -> InlineKeyboardMarkup:
    rows = []
    for c in colors:
        mark = "✅" if c.is_available else "🚫"
        rows.append([InlineKeyboardButton(text=f"{mark} {c.name}", callback_data=f"toggle_color:{code}:{c.name}")])
    rows.append([InlineKeyboardButton(text="➕ Yangi rang qo'shish", callback_data=f"add_color:{code}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_product:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def size_manage_keyboard(code: str, sizes: list) -> InlineKeyboardMarkup:
    rows = []
    for s in sizes:
        mark = "✅" if s.is_available else "🚫"
        rows.append([InlineKeyboardButton(text=f"{mark} {s.name}", callback_data=f"toggle_size:{code}:{s.name}")])
    rows.append([InlineKeyboardButton(text="➕ Yangi o'lcham qo'shish", callback_data=f"add_size:{code}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_product:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_admin_actions(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"order_accept:{order_id}"),
         InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"order_cancel:{order_id}")],
    ])


def payment_check_actions(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"pay_confirm:{order_id}"),
         InlineKeyboardButton(text="❌ Rad etish", callback_data=f"pay_reject:{order_id}")],
    ])


def delivery_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"deliver_going:{order_id}"),
         InlineKeyboardButton(text="📦 Yetkazildi", callback_data=f"deliver_done:{order_id}")],
    ])


def order_pay_button(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Pul tashlash", callback_data=f"pay_start:{order_id}")],
        [InlineKeyboardButton(text="🚫 Buyurtmani bekor qilish", callback_data=f"user_cancel:{order_id}")],
    ])


def channel_order_button(code: str, bot_username: str) -> InlineKeyboardMarkup:
    # Kanal - ochiq maydon, botga callback yubora olmaydi (foydalanuvchi botni ishga
    # tushirmagan bo'lishi mumkin). Shuning uchun deep-link orqali botni ochamiz -
    # u yerda /start payload'ni o'qib, xuddi shu buyurtma oqimini boshlaydi.
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Buyurtma berish",
                               url=f"https://t.me/{bot_username}?start=order_{code}")]
    ])


def color_choice_keyboard(code: str, colors: list[str]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=c, callback_data=f"choose_color:{code}:{c}")] for c in colors]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def size_choice_keyboard(code: str, sizes: list[str]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=s, callback_data=f"choose_size:{code}:{s}")] for s in sizes]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_order_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data=f"confirm_order:{code}")],
        [InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="cancel_order_flow")],
    ])
