import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import settings
from app.handlers import (
    start, help as help_handler, admin,
    admin_products, admin_orders, admin_discounts, admin_support,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Do'konni ochish"),
        BotCommand(command="help", description="Yordam so'rash"),
    ])
    # /admin ataylab umumiy buyruqlar ro'yxatiga qo'shilmaydi — u faqat ADMIN_IDS uchun ishlaydi


async def main():
    if not settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi — .env faylini tekshiring")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(help_handler.router)
    dp.include_router(admin.router)
    dp.include_router(admin_products.router)
    dp.include_router(admin_orders.router)
    dp.include_router(admin_discounts.router)
    dp.include_router(admin_support.router)

    await set_commands(bot)
    logger.info(f"{settings.SHOP_NAME} boti ishga tushdi")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
