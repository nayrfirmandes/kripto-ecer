from typing import Any
from aiogram import Router, F
from aiogram.types import CallbackQuery
from prisma import Prisma
from prisma.enums import UserStatus

from bot.keyboards.admin import back_to_admin_keyboard
from bot.handlers.admin.shared import is_admin, safe_edit_text

router = Router()


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    total = await db.user.count()
    active = await db.user.count(where={"status": UserStatus.ACTIVE})
    banned = await db.user.count(where={"status": UserStatus.BANNED})
    
    recent_users = await db.user.find_many(
        order={"createdAt": "desc"},
        take=5
    )
    
    text = (
        "<b>👥 User Management</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Total Users: <b>{total}</b>\n"
        f"Active: <b>{active}</b>\n"
        f"Banned: <b>{banned}</b>\n\n"
        "<b>Recent Users:</b>\n"
    )
    
    for u in recent_users:
        status = "🟢" if u.status == UserStatus.ACTIVE else "🔴"
        user_name = u.firstName or u.username or "Unknown"
        text += f"{status} {user_name} (@{u.username or 'N/A'})\n"
    
    await safe_edit_text(callback, text, reply_markup=back_to_admin_keyboard())
    await callback.answer()
