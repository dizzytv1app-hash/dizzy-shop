from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import get_session
from app.services.orders import get_order, submit_payment_receipt, request_cancel
from app.services.settings_service import get_setting, KEY_CARD_NUMBER, KEY_CARD_OWNER
from app.services.users import list_admins
from app.bot.states import PaymentFlow
from app.bot.utils.formatting import fmt_price, order_card_text
from app.bot.keyboards import payment_check_actions, main_user_keyboard

router = Router(name="payment")


@router.callback_query(F.data.startswith("pay_start:"))
async def cb_pay_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        card_number = get_setting(db, KEY_CARD_NUMBER)
        card_owner = get_setting(db, KEY_CARD_OWNER)
        prepay = order.prepay_amount or order.price

    if not card_number:
        await callback.message.answer("⚠️ Hozircha to'lov uchun karta ma'lumotlari sozlanmagan. "
                                       "Iltimos, admin bilan bog'laning.")
        await callback.answer()
        return

    await state.update_data(order_id=order_id)
    await state.set_state(PaymentFlow.waiting_receipt)
    await callback.message.answer(
        f"💳 To'lov miqdori: <b>{fmt_price(prepay)}</b>\n"
        f"Karta raqami: <code>{card_number}</code>\n"
        f"Karta egasi: {card_owner or '-'}\n\n"
        f"To'lovni amalga oshirgach, chekning rasmini shu yerga yuboring 📸"
    )
    await callback.answer()


@router.message(PaymentFlow.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    order_id = data.get("order_id")
    file_id = message.photo[-1].file_id

    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await state.clear()
            await message.answer("Buyurtma topilmadi.")
            return
        submit_payment_receipt(db, order, file_id)
        text = "🧾 Yangi to'lov cheki!\n\n" + order_card_text(order)
        admins = list_admins(db)
        admin_ids = [a.telegram_id for a in admins]

    await state.clear()
    await message.answer("✅ Chekingiz qabul qilindi. Admin tasdiqlashini kuting.",
                          reply_markup=main_user_keyboard())

    for admin_id in admin_ids:
        try:
            await bot.send_photo(admin_id, file_id, caption=text, reply_markup=payment_check_actions(order_id))
        except Exception:
            pass


@router.message(PaymentFlow.waiting_receipt)
async def receipt_wrong_input(message: Message):
    await message.answer("Iltimos, to'lov chekining rasmini yuboring 📸")


@router.callback_query(F.data.startswith("user_cancel:"))
async def cb_user_cancel(callback: CallbackQuery, bot):
    order_id = int(callback.data.split(":", 1)[1])
    with get_session() as db:
        order = get_order(db, order_id)
        if not order:
            await callback.answer("Buyurtma topilmadi.", show_alert=True)
            return
        request_cancel(db, order)
        text = "🚫 Mijoz buyurtmani bekor qilishni so'radi!\n\n" + order_card_text(order)
        admins = list_admins(db)
        admin_ids = [a.telegram_id for a in admins]

    await callback.answer("So'rovingiz adminlarga yuborildi.")
    await callback.message.answer("So'rovingiz qabul qilindi, admin tez orada ko'rib chiqadi.")

    from app.bot.keyboards import order_admin_actions
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=order_admin_actions(order_id))
        except Exception:
            pass
