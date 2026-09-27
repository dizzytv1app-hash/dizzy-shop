import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, InputMediaPhoto

from app.database import get_session
from app.services.products import get_product_by_code
from app.bot.utils.filters import IsAdmin
from app.bot.utils.formatting import product_card_text

router = Router(name="product_search")

# K001, k12, A1234 kabi kodlarga mos keladi. FSM holati bo'sh bo'lgandagina ishlaydi,
# aks holda boshqa qadamlar (masalan mahsulot qo'shish) bilan chalkashib ketmaydi.
CODE_PATTERN = re.compile(r"^[A-Za-z]{1,3}\d{1,5}$")


@router.message(IsAdmin(), StateFilter(None), F.text.regexp(CODE_PATTERN.pattern))
async def search_product_code(message: Message):
    code = message.text.strip().upper()
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            return  # Oddiy matn bo'lishi ham mumkin - jim turamiz
        text = product_card_text(product)
        images = [img.file_id for img in product.images]

    if images:
        if len(images) == 1:
            await message.answer_photo(images[0], caption=text)
        else:
            media = [InputMediaPhoto(media=fid, caption=text if i == 0 else None)
                     for i, fid in enumerate(images)]
            await message.answer_media_group(media)
    else:
        await message.answer(text)
