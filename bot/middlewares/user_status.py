from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timedelta, timezone
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from prisma import Prisma
from cachetools import TTLCache


class UserStatusMiddleware(BaseMiddleware):
    INACTIVE_MONTHS = 6
    ACTIVITY_UPDATE_INTERVAL = 3600
    
    def __init__(self):
        super().__init__()
        self._last_activity_cache: Dict[int, datetime] = {}
        self._user_cache: TTLCache = TTLCache(maxsize=10000, ttl=30)  # Reduced from 300s to 30s for real-time
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db: Prisma = data.get("db")
        
        if not db:
            return await handler(event, data)
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if not user_id:
            return await handler(event, data)
        
        now = datetime.now(timezone.utc)
        cached_time = self._last_activity_cache.get(user_id)
        
        # Check cache first (30s TTL for real-time data)
        cached_user = self._user_cache.get(user_id)
        if cached_user:
            data["user"] = cached_user
            # Schedule activity update in background (don't block handler)
            if cached_time and (now - cached_time).total_seconds() >= self.ACTIVITY_UPDATE_INTERVAL:
                from bot.tasks.background_tasks import schedule_background_task
                async def update_activity_background():
                    try:
                        await db.user.update(
                            where={"telegramId": user_id},
                            data={"lastActiveAt": now}
                        )
                    except:
                        pass
                schedule_background_task(update_activity_background())
            return await handler(event, data)
        
        # Cache miss - fetch from DB (only status + balance, required for real-time)
        user = await db.user.find_unique(
            where={"telegramId": user_id},
            include={"balance": True}
        )
        
        if user:
            # Check if user should be marked inactive (minimal check)
            inactive_threshold = now - timedelta(days=self.INACTIVE_MONTHS * 30)
            last_active = user.lastActiveAt
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            
            # Mark inactive in background if needed
            if last_active < inactive_threshold and user.status == "ACTIVE":
                from bot.tasks.background_tasks import schedule_background_task
                async def mark_inactive_background():
                    try:
                        await db.user.update(
                            where={"telegramId": user_id},
                            data={"status": "INACTIVE"}
                        )
                    except:
                        pass
                schedule_background_task(mark_inactive_background())
            
            self._last_activity_cache[user_id] = now
            self._user_cache[user_id] = user
            data["user"] = user
        
        return await handler(event, data)
    
    def invalidate_user(self, telegram_id: int):
        self._user_cache.pop(telegram_id, None)
        self._last_activity_cache.pop(telegram_id, None)
    
    def update_user_cache(self, telegram_id: int, user):
        self._user_cache[telegram_id] = user
        self._last_activity_cache[telegram_id] = datetime.now(timezone.utc)
