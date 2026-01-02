from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from prisma import Prisma

from bot.services.oxapay import OxaPayService
from bot.config import config


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
        self.oxapay = OxaPayService(
            merchant_api_key=config.oxapay.merchant_api_key,
            payout_api_key=config.oxapay.payout_api_key,
            webhook_secret=config.oxapay.webhook_secret,
        )
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.prisma
        data["oxapay"] = self.oxapay
        return await handler(event, data)
