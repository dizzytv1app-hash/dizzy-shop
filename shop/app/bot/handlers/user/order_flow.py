from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import get_session
from app.services.users import get_or_create_user
from app.services.products import get_product_by_code
from app.services.orders import create_order
from app.models import OrderSource
from app.bot.states import UserOrderFlow
from app.bot.keyboards import color_choice_keyboard, size_choice_keyboard, confirm_order_keyboard, main_user_keyboard
from app.bot.utils.formatting import fmt_price

router = Router(name="order_flow")


async def begin_order(message: Message, state: FSMContext, code: str):
    """Kod berilgan mahsulot uchun buyurtma jarayonini boshlaydi (rang tanlashdan)."""
    with get_session() as db:
        product = get_product_by_code(db, code, active_only=True)
        if not product:
            await message.answer("❗️ Bu mahsulot topilmadi yoki endi mavjud emas.")
            return
        available_colors = [c.name for c in product.colors if c.is_available]
        name = product.name

    if not available_colors:
        await message.answer("😔 Afsuski, bu mahsulotning hech qanday rangi hozircha mavjud emas.")
        return

    await state.update_data(code=code)
    await state.set_state(UserOrderFlow.choosing_color)
    await message.answer(
        f"🛒 <b>{name}</b> ({code})\n\nIltimos, rangni tanlang:",
        reply_markup=color_choice_keyboard(code, available_colors),
    )


@router.callback_query(F.data.startswith("choose_color:"))
async def cb_choose_color(callback: CallbackQuery, state: FSMContext):
    _, code, color = callback.data.split(":", 2)
    with get_session() as db:
        product = get_product_by_code(db, code, active_only=True)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        available_sizes = [s.name for s in product.sizes if s.is_available]

    if not available_sizes:
        await callback.message.answer("😔 Afsuski, bu mahsulotning hech qanday o'lchami hozircha mavjud emas.")
        await callback.answer()
        return

    await state.update_data(color=color)
    await state.set_state(UserOrderFlow.choosing_size)
    await callback.message.answer("Endi o'lchamni tanlang:", reply_markup=size_choice_keyboard(code, available_sizes))
    await callback.answer()


@router.callback_query(F.data.startswith("choose_size:"))
async def cb_choose_size(callback: CallbackQuery, state: FSMContext):
    _, code, size = callback.data.split(":", 2)
    data = await state.get_data()
    with get_session() as db:
        product = get_product_by_code(db, code, active_only=True)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        price = product.price
        name = product.name

    await state.update_data(size=size)
    await state.set_state(UserOrderFlow.confirm)
    text = (
        f"📝 Buyurtmangizni tasdiqlang:\n\n"
        f"Mahsulot: <b>{name}</b> ({code})\n"
        f"Rang: {data.get('color')}\n"
        f"O'lcham: {size}\n"
        f"Narx: <b>{fmt_price(price)}</b>\n\n"
        f"⚠️ Tanlangan rang/o'lcham mavjudligi tasdiqlangandan so'ng buyurtma qabul qilinadi."
    )
    await callback.message.answer(text, reply_markup=confirm_order_keyboard(code))
    await callback.answer()


@router.callback_query(F.data == "cancel_order_flow")
async def cb_cancel_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Bekor qilindi.", reply_markup=main_user_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_order:"))
async def cb_confirm_order(callback: CallbackQuery, state: FSMContext, bot):
    code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    color, size = data.get("color"), data.get("size")

    with get_session() as db:
        user = get_or_create_user(
            db, callback.from_user.id, callback.from_user.username, callback.from_user.full_name
        )
        product = get_product_by_code(db, code, active_only=True)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        order, err = create_order(db, user, product, color, size, OrderSource.BOT)
        if not order:
            await callback.message.answer(f"❗️ {err}")
            await state.clear()
            await callback.answer()
            return
        order_id = order.id
        order_number = order.order_number

    await state.clear()
    await callback.message.answer(
        f"✅ Buyurtmangiz qabul qilindi!\nBuyurtma raqami: <code>{order_number}</code>\n\n"
        f"Tez orada admin buyurtmangizni ko'rib chiqadi va siz bilan bog'lanadi.",
        reply_markup=main_user_keyboard(),
    )
    await callback.answer()

    # Adminlarga xabar yuboramiz
    from app.services.users import list_admins
    from app.bot.keyboards import order_admin_actions
    from app.bot.utils.formatting import order_card_text
    from app.services.orders import get_order

    with get_session() as db:
        order = get_order(db, order_id)
        text = "🆕 Yangi buyurtma!\n\n" + order_card_text(order)
        admins = list_admins(db)
        admin_ids = [a.telegram_id for a in admins]

    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=order_admin_actions(order_id))
        except Exception:
            pass  # Admin botni bloklagan yoki hali /start bosmagan bo'lishi mumkin
