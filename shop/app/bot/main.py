import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database import init_db, get_session
from app.services.users import ensure_owner_bootstrapped

# Foydalanuvchi handlerlari
from app.bot.handlers.user import start as user_start
from app.bot.handlers.user import help as user_help
from app.bot.handlers.user import order_flow as user_order_flow
from app.bot.handlers.user import payment as user_payment

# Admin handlerlari
from app.bot.handlers.admin import menu as admin_menu
from app.bot.handlers.admin import add_product as admin_add_product
from app.bot.handlers.admin import manage_products as admin_manage_products
from app.bot.handlers.admin import analyze as admin_analyze
from app.bot.handlers.admin import discounts as admin_discounts
from app.bot.handlers.admin import admins as admin_admins
from app.bot.handlers.admin import settings as admin_settings
from app.bot.handlers.admin import send_to_channel as admin_send_to_channel
from app.bot.handlers.admin import orders as admin_orders
from app.bot.handlers.admin import stats as admin_stats
from app.bot.handlers.admin import product_search as admin_product_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: aniqroq (state/matn) handlerlar avval, umumiy narsalar (kod qidirish) oxirida
    dp.include_router(admin_menu.router)
    dp.include_router(admin_add_product.router)
    dp.include_router(admin_manage_products.router)
    dp.include_router(admin_analyze.router)
    dp.include_router(admin_discounts.router)
    dp.include_router(admin_admins.router)
    dp.include_router(admin_settings.router)
    dp.include_router(admin_send_to_channel.router)
    dp.include_router(admin_orders.router)
    dp.include_router(admin_stats.router)

    dp.include_router(user_start.router)
    dp.include_router(user_help.router)
    dp.include_router(user_order_flow.router)
    dp.include_router(user_payment.router)

    # Mahsulot kodini qidirish eng oxirida - chunki u har qanday qisqa matnga reaksiya beradi
    dp.include_router(admin_product_search.router)

    return dp


async def main():
    if not settings.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN sozlanmagan! .env fayliga BOT_TOKEN=... qo'shing (BotFather'dan oling)."
        )

    init_db()
    with get_session() as db:
        ensure_owner_bootstrapped(db, settings.OWNER_TELEGRAM_ID)

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()

    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
