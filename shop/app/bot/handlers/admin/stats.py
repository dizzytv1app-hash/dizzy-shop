from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.database import get_session
from app.services.stats import get_full_stats
from app.bot.utils.filters import IsAdmin
from app.bot.utils.formatting import fmt_price

router = Router(name="stats")


@router.message(F.text == "📈 Statistika", IsAdmin(), StateFilter(None))
async def show_stats(message: Message):
    with get_session() as db:
        s = get_full_stats(db)

    top_products = "\n".join(
        f"{i+1}. {name} ({code}) — {cnt} ta" for i, (name, code, cnt) in enumerate(s["top_products"])
    ) or "—"
    top_customers = "\n".join(
        f"{i+1}. {full_name or username or tg_id} — {cnt} ta buyurtma"
        for i, (full_name, username, tg_id, cnt) in enumerate(s["top_customers"])
    ) or "—"

    text = (
        "📈 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{s['total_users']}</b>\n"
        f"🆕 Bugungi yangi foydalanuvchilar: <b>{s['new_users_today']}</b>\n"
        f"👕 Jami kiyimlar: <b>{s['total_products']}</b>\n\n"
        f"📦 Jami buyurtmalar: <b>{s['total_orders']}</b>\n"
        f"⏳ Kutilayotgan: <b>{s['pending_orders']}</b>\n"
        f"💰 To'lovi tasdiqlangan: <b>{s['confirmed_orders']}</b>\n"
        f"✅ Yetkazilgan: <b>{s['delivered_orders']}</b>\n"
        f"❌ Bekor qilingan: <b>{s['cancelled_orders']}</b>\n\n"
        f"💵 Bugungi savdo: <b>{fmt_price(s['today_sales'])}</b>\n"
        f"💵 Oylik savdo: <b>{fmt_price(s['month_sales'])}</b>\n"
        f"💵 Umumiy savdo: <b>{fmt_price(s['total_sales'])}</b>\n\n"
        f"🏆 <b>TOP 10 sotilgan kiyim:</b>\n{top_products}\n\n"
        f"🏆 <b>TOP 10 mijoz:</b>\n{top_customers}"
    )
    await message.answer(text)
