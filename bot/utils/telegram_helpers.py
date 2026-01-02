"""
Helper utilities for Telegram bot operations.
Provides type-safe wrappers for common operations.
"""
from typing import Optional, Any
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup


async def safe_edit_text(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML"
) -> bool:
    """
    Safely edit callback message text.
    Returns True if successful, False otherwise.
    """
    msg = callback.message
    if msg is None:
        return False
    
    if not isinstance(msg, Message):
        return False
    
    try:
        await msg.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception:
        return False


async def safe_delete_message(callback: CallbackQuery) -> bool:
    """
    Safely delete callback message.
    Returns True if successful, False otherwise.
    """
    msg = callback.message
    if msg is None:
        return False
    
    if not isinstance(msg, Message):
        return False
    
    try:
        await msg.delete()
        return True
    except Exception:
        return False


def get_callback_data(callback: CallbackQuery) -> str:
    """
    Safely get callback data, returns empty string if None.
    """
    return callback.data or ""


def parse_callback_parts(callback: CallbackQuery, separator: str = ":") -> list[str]:
    """
    Parse callback data into parts.
    Returns empty list if callback data is None.
    """
    data = callback.data
    if not data:
        return []
    return data.split(separator)


def get_callback_part(callback: CallbackQuery, index: int, separator: str = ":") -> Optional[str]:
    """
    Get specific part of callback data.
    Returns None if index out of bounds or data is None.
    """
    parts = parse_callback_parts(callback, separator)
    if index < 0 or index >= len(parts):
        return None
    return parts[index]


def get_message_text(message: Message) -> str:
    """
    Safely get message text, returns empty string if None.
    """
    return message.text or ""


def get_user_display_name(user: Any) -> str:
    """
    Get user display name from Prisma User object.
    Falls back to username, then 'User' if no name available.
    """
    if user is None:
        return "User"
    
    first_name = getattr(user, 'firstName', None)
    if first_name:
        return first_name
    
    username = getattr(user, 'username', None)
    if username:
        return username
    
    return "User"


def get_user_balance(user: Any) -> int:
    """
    Safely get user balance amount.
    Returns 0 if balance not available.
    """
    if user is None:
        return 0
    
    balance = getattr(user, 'balance', None)
    if balance is None:
        return 0
    
    amount = getattr(balance, 'amount', 0)
    return int(amount) if amount else 0
