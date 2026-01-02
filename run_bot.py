import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Optional
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from prisma import Prisma

from bot.config import config
from bot.handlers import setup_routers
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.user_status import UserStatusMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.webhook import handle_oxapay_webhook, health_check
from bot.tasks.background_tasks import warm_coins_cache, refresh_coins_cache_worker, database_keepalive_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/telegram/webhook"
WEBHOOK_PORT = 8080


def setup_dispatcher(prisma: Prisma) -> Dispatcher:
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
    
    return dp


_prisma_instance: Optional[Prisma] = None


async def on_startup(bot: Bot):
    webhook_url = f"https://{config.webhook_host}{WEBHOOK_PATH}"
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )
    logger.info(f"Webhook set to: {webhook_url}")
    
    # WARM COINS CACHE FOR INSTANT RESPONSES
    await warm_coins_cache()
    
    # START BACKGROUND WORKERS (fire and forget)
    asyncio.create_task(refresh_coins_cache_worker())
    
    # DATABASE KEEPALIVE - ping every 60s to prevent NeonSQL idle disconnect
    if _prisma_instance:
        asyncio.create_task(database_keepalive_worker(_prisma_instance))
        logger.info("Database keepalive worker started")


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
    
    if not config.webhook_host:
        logger.error("WEBHOOK_HOST or REPLIT_DEV_DOMAIN is not set!")
        return
    
    global _prisma_instance
    prisma = Prisma()
    _prisma_instance = prisma
    
    try:
        await prisma.connect()
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return
    
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = setup_dispatcher(prisma)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    app["db"] = prisma
    app["bot"] = bot
    
    app.router.add_post("/webhook/oxapay", handle_oxapay_webhook)
    app.router.add_get("/health", health_check)
    
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    
    logger.info(f"Starting Crypto Trading Bot in WEBHOOK mode...")
    logger.info(f"Webhook host: {config.webhook_host}")
    logger.info(f"Telegram webhook path: {WEBHOOK_PATH}")
    logger.info(f"Admin IDs: {config.bot.admin_ids}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    
    logger.info(f"Bot webhook server running on 0.0.0.0:{WEBHOOK_PORT}")
    
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await prisma.disconnect()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
