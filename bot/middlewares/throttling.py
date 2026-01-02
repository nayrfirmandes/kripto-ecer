from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.cache = TTLCache(maxsize=10000, ttl=rate_limit)
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if user_id:
            if user_id in self.cache:
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ Mohon tunggu sebentar...", show_alert=False)
                return
            
            self.cache[user_id] = True
        
        return await handler(event, data)
