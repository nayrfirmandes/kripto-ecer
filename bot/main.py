import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from prisma import Prisma

from bot.config import config
from bot.handlers import setup_routers
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.user_status import UserStatusMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.webhook import handle_oxapay_webhook, health_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook/telegram"
WEBHOOK_PORT = 8080


async def on_startup(bot: Bot):
    webhook_url = f"https://{config.webhook_host}{WEBHOOK_PATH}"
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )
    logger.info(f"Webhook set to: {webhook_url}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


async def main():
    if not config.bot.token:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        return
    
    if not config.database.url:
        logger.error("BOT_DATABASE is not set!")
        return
    
    prisma = Prisma()
    await prisma.connect()
    logger.info("Connected to database")
    
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    logging_mw = LoggingMiddleware()
    throttling_mw = ThrottlingMiddleware(rate_limit=0.1)
    database_mw = DatabaseMiddleware(prisma)
    user_status_mw = UserStatusMiddleware()
    
    dp.message.middleware(logging_mw)
    dp.callback_query.middleware(logging_mw)
    
    dp.message.middleware(throttling_mw)
    dp.callback_query.middleware(throttling_mw)
    
    dp.message.middleware(database_mw)
    dp.callback_query.middleware(database_mw)
    
    dp.message.middleware(user_status_mw)
    dp.callback_query.middleware(user_status_mw)
    
    router = setup_routers()
    dp.include_router(router)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    app["db"] = prisma
    app["bot"] = bot
    
    app.router.add_post("/webhook/oxapay", handle_oxapay_webhook)
    app.router.add_get("/health", health_check)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    
    logger.info(f"Starting Crypto Trading Bot in WEBHOOK mode...")
    logger.info(f"Admin IDs: {config.bot.admin_ids}")
    logger.info(f"Webhook host: {config.webhook_host}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    
    logger.info(f"Bot webhook server running on 0.0.0.0:{WEBHOOK_PORT}")
    
    try:
        await asyncio.Event().wait()
    finally:
        await prisma.disconnect()
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
