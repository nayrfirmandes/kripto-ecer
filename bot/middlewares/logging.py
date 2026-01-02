import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        event_type = type(event).__name__
        event_data = ""
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if event.text:
                event_data = f"text='{event.text[:50]}'"
            elif event.location:
                event_data = f"location=({event.location.latitude}, {event.location.longitude})"
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            event_data = f"data='{event.data}'"
        
        logger.info(f"[{event_type}] user_id={user_id} {event_data}")
        
        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            logger.error(f"[{event_type}] Error for user_id={user_id}: {str(e)}")
            raise
