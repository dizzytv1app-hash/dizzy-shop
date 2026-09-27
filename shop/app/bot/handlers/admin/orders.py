from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery

from app.database import get_session
from app.services.orders import (
    list_orders, get_order, accept_order, admin_cancel_order, confirm_payment,
    reject_payment, set_delivery_status,
)
from app.models import OrderStatus
from app.bot.utils.filters import IsAdmin
from app.bot.utils.formatting import order_card_text, fmt_price
from app.bot.keyboards import (
    order_admin_actions, payment_check_actions, delivery_status_keyboard, order_pay_button,
)

router = Router(name="admin_orders")


@router.message(F.text == "📦 Buyurtmalar", IsAdmin(), StateFilter(None))
async def show_orders(message: Message):
    with get_session() as db:
        pending = list_orders(db, status=None, limit=15)

    if not pending:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return

    await message.answer(f"📦 So'nggi {len(pending)} ta buyurtma:")
    for order in pending:
        text = order_card_text(order)
        markup = None
        if order.status == OrderStatus.NEW:
            markup = order_admin_actions(order.id)
        elif order.status == OrderStatus.PAYMENT_PENDING and order.payment_receipt_file_id:
            markup = payment_check_actions(order.id)
        elif order.status == OrderStatus.PAYMENT_CONFIRMED:
            markup = delivery_status_keyboard(order.id)

        if order.status == OrderStatus.PAYMENT_PENDING and order.payment_receipt_file_id:
            await message.answer_photo(order.payment_receipt_file_id, caption=text, reply_markup=markup)
        else:
            await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("order_accept:"), IsAdmin())
async def cb_accept_order(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        prepay = accept_order(db, order)
        user_tg_id = order.user.telegram_id
        product_name = order.product_name
        order_number = order.order_number

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Buyurtma qabul qilindi.")

    from app.services.settings_service import get_setting, KEY_CARD_NUMBER, KEY_CARD_OWNER
    with get_session() as db:
        card_number = get_setting(db, KEY_CARD_NUMBER)
        card_owner = get_setting(db, KEY_CARD_OWNER)

    text = (
        f"✅ Buyurtmangiz (<code>{order_number}</code>) qabul qilindi!\n"
        f"Mahsulot: {product_name}\n\n"
        f"💰 Oldindan to'lov: <b>{fmt_price(prepay)}</b> (umumiy narxning 50%)\n"
    )
    if card_number:
        text += f"\n💳 Karta: <code>{card_number}</code>"
        if card_owner:
            text += f"\n👤 Karta egasi: {card_owner}"
    else:
        text += "\n⚠️ Karta ma'lumotlari hali admin tomonidan kiritilmagan."
    text += (
        "\n\n📦 Yetkazib berish do'kon tomonidan amalga oshiriladi. Aniq vaqt keyinroq siz bilan "
        "bog'lanish orqali kelishiladi."
    )
    try:
        await bot.send_message(user_tg_id, text, reply_markup=order_pay_button(order_id))
    except Exception:
        pass


@router.callback_query(F.data.startswith("order_cancel:"), IsAdmin())
async def cb_admin_cancel(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        admin_cancel_order(db, order)
        user_tg_id = order.user.telegram_id
        order_number = order.order_number

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Buyurtma bekor qilindi.")
    try:
        await bot.send_message(user_tg_id, f"❌ Buyurtmangiz (<code>{order_number}</code>) bekor qilindi.")
    except Exception:
        pass


@router.callback_query(F.data.startswith("pay_confirm:"), IsAdmin())
async def cb_confirm_payment(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        confirm_payment(db, order)
        user_tg_id = order.user.telegram_id
        order_number = order.order_number

    await callback.message.edit_reply_markup(reply_markup=delivery_status_keyboard(order_id))
    await callback.answer("To'lov tasdiqlandi.")
    try:
        await bot.send_message(
            user_tg_id,
            f"💰 Buyurtmangiz (<code>{order_number}</code>) uchun to'lov tasdiqlandi. Tez orada yetkazib "
            f"berish boshlanadi.",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("pay_reject:"), IsAdmin())
async def cb_reject_payment(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        reject_payment(db, order)
        user_tg_id = order.user.telegram_id
        order_number = order.order_number

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("To'lov rad etildi.")
    try:
        await bot.send_message(
            user_tg_id,
            f"❗️ Buyurtmangiz (<code>{order_number}</code>) uchun yuborgan chekingiz tasdiqlanmadi. "
            f"Iltimos, to'lovni tekshirib, chekni qaytadan yuboring.",
            reply_markup=order_pay_button(order_id),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("deliver_going:"), IsAdmin())
async def cb_deliver_going(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        set_delivery_status(db, order, OrderStatus.DELIVERING)
        user_tg_id = order.user.telegram_id
        order_number = order.order_number

    await callback.answer("Holat yangilandi: Yetkazilmoqda.")
    try:
        await bot.send_message(user_tg_id, f"🚚 Buyurtmangiz (<code>{order_number}</code>) yetkazib berilmoqda.")
    except Exception:
        pass


@router.callback_query(F.data.startswith("deliver_done:"), IsAdmin())
async def cb_deliver_done(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        set_delivery_status(db, order, OrderStatus.DELIVERED)
        user_tg_id = order.user.telegram_id
        order_number = order.order_number

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Holat yangilandi: Yetkazildi.")
    try:
        await bot.send_message(user_tg_id, f"📦 Buyurtmangiz (<code>{order_number}</code>) yetkazildi. "
                                            f"Xaridingiz uchun rahmat! 🙏")
    except Exception:
        pass
