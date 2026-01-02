import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from prisma import Prisma

from bot.services.oxapay import OxaPayService
from bot.config import config

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
        self.oxapay = OxaPayService(
            merchant_api_key=config.oxapay.merchant_api_key,
            payout_api_key=config.oxapay.payout_api_key,
            webhook_secret=config.oxapay.webhook_secret,
        )
        super().__init__()
    
    async def ensure_connected(self) -> None:
        """Ensure database connection is alive, reconnect if needed."""
        try:
            if not self.prisma.is_connected():
                logger.warning("Database disconnected, reconnecting...")
                await self.prisma.connect()
                logger.info("Database reconnected successfully")
        except Exception as e:
            logger.error(f"Database reconnection failed: {e}")
            try:
                await self.prisma.disconnect()
            except Exception:
                pass
            await self.prisma.connect()
            logger.info("Database reconnected after disconnect")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        await self.ensure_connected()
        data["db"] = self.prisma
        data["oxapay"] = self.oxapay
        return await handler(event, data)
