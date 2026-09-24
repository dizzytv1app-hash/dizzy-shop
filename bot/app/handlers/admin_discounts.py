from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.handlers.admin import is_admin
from app.states import AddDiscount
from app.keyboards import discount_target_keyboard, category_pick_keyboard, back_to_menu_keyboard, CATEGORIES
from app.api_client import create_discount, list_discounts, toggle_discount, delete_discount, ApiError

router = Router(name="admin_discounts")
CATEGORY_LABELS = dict(CATEGORIES)


def _discount_row_keyboard(d: dict) -> InlineKeyboardMarkup:
    toggle_text = "⛔️ O'chirish" if d["active"] else "✅ Yoqish"
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=toggle_text, callback_data=f"adm:disc_toggle:{d['id']}:{0 if d['active'] else 1}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm:disc_delete:{d['id']}"),
        ]]
    )


@router.callback_query(F.data == "adm:discounts")
async def cb_discounts_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await call.answer()
    try:
        data = await list_discounts(call.from_user.id)
    except ApiError as e:
        await call.message.edit_text(f"Xato: {e.detail}", reply_markup=back_to_menu_keyboard())
        return

    items = data.get("items", [])
    kb_rows = [[InlineKeyboardButton(text="➕ Yangi chegirma", callback_data="adm:add_discount")]]
    await call.message.edit_text(
        "🏷️ Chegirmalar" + ("\n\nHozircha chegirma yo'q." if not items else ""),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows + [[InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:menu")]]),
    )
    for d in items:
        target = CATEGORY_LABELS.get(d.get("category"), d.get("category")) if d.get("category") else f"mahsulot #{d.get('product_id')}"
        state_label = "✅ faol" if d["active"] else "⛔️ o'chiq"
        text = f"#{d['id']} — {target} — {d['percent']}% — {state_label}"
        await call.message.answer(text, reply_markup=_discount_row_keyboard(d))


@router.callback_query(F.data == "adm:add_discount")
async def start_add_discount(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.set_state(AddDiscount.target_type)
    await call.answer()
    await call.message.edit_text("Chegirma nimaga qo'llansin?", reply_markup=discount_target_keyboard())


@router.callback_query(AddDiscount.target_type, F.data == "disc_target:category")
async def discount_by_category(call: CallbackQuery, state: FSMContext):
    await state.update_data(target_type="category")
    await state.set_state(AddDiscount.target_value)
    await call.answer()
    await call.message.edit_text("Qaysi kategoriya?", reply_markup=category_pick_keyboard("disccat"))


@router.callback_query(AddDiscount.target_value, F.data.startswith("disccat:"))
async def discount_category_chosen(call: CallbackQuery, state: FSMContext):
    category = call.data.split(":")[1]
    await state.update_data(target_value=category)
    await state.set_state(AddDiscount.percent)
    await call.answer()
    await call.message.edit_text(f"Kategoriya: {CATEGORY_LABELS.get(category, category)}\n\nChegirma foizini kiriting (1-90):")


@router.callback_query(AddDiscount.target_type, F.data == "disc_target:product")
async def discount_by_product(call: CallbackQuery, state: FSMContext):
    await state.update_data(target_type="product")
    await state.set_state(AddDiscount.target_value)
    await call.answer()
    await call.message.edit_text("Mahsulot ID raqamini kiriting (📦 Mahsulotlar bo'limida ko'rasiz):")


@router.message(AddDiscount.target_value)
async def discount_product_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❗️ Faqat raqam kiriting:")
        return
    await state.update_data(target_value=int(message.text.strip()))
    await state.set_state(AddDiscount.percent)
    await message.answer("Chegirma foizini kiriting (1-90):")


@router.message(AddDiscount.percent)
async def discount_percent(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw.isdigit() or not (1 <= int(raw) <= 90):
        await message.answer("❗️ 1 dan 90 gacha son kiriting:")
        return

    data = await state.get_data()
    payload = {"percent": int(raw)}
    if data["target_type"] == "category":
        payload["category"] = data["target_value"]
    else:
        payload["product_id"] = data["target_value"]

    try:
        await create_discount(message.from_user.id, payload)
        await message.answer(f"✅ Chegirma qo'shildi: {raw}%")
    except ApiError as e:
        await message.answer(f"❌ Xato: {e.detail}")
    await state.clear()


@router.callback_query(F.data.startswith("adm:disc_toggle:"))
async def cb_toggle_discount(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    _, _, discount_id, new_state = call.data.split(":")
    try:
        await toggle_discount(call.from_user.id, int(discount_id), active=bool(int(new_state)))
        await call.answer("Yangilandi ✅")
        await call.message.edit_text(call.message.text + "\n\n(holat yangilandi)")
    except ApiError as e:
        await call.answer(f"Xato: {e.detail}", show_alert=True)


@router.callback_query(F.data.startswith("adm:disc_delete:"))
async def cb_delete_discount(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    discount_id = int(call.data.split(":")[2])
    try:
        await delete_discount(call.from_user.id, discount_id)
        await call.answer("O'chirildi ✅")
        await call.message.edit_text(f"🗑 Chegirma #{discount_id} o'chirildi.")
    except ApiError as e:
        await call.answer(f"Xato: {e.detail}", show_alert=True)
