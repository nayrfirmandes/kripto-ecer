from typing import Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from prisma import Prisma
from prisma.enums import TransactionStatus

from bot.keyboards.admin import admin_menu_keyboard
from bot.handlers.admin.shared import is_admin, safe_edit_text

router = Router()


@router.message(Command("admin"))
async def admin_menu(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    pending_topup = await db.deposit.count(where={"status": TransactionStatus.PENDING})
    pending_withdraw = await db.withdrawal.count(where={"status": TransactionStatus.PENDING})
    total_users = await db.user.count()
    
    await message.answer(
        f"🔐 <b>ADMIN PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📥 Pending Topup: <b>{pending_topup}</b>\n"
        f"📤 Pending Withdraw: <b>{pending_withdraw}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih menu di bawah:",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(pending_topup, pending_withdraw)
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    pending_topup = await db.deposit.count(where={"status": TransactionStatus.PENDING})
    pending_withdraw = await db.withdrawal.count(where={"status": TransactionStatus.PENDING})
    total_users = await db.user.count()
    
    await safe_edit_text(
        callback,
        f"🔐 <b>ADMIN PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📥 Pending Topup: <b>{pending_topup}</b>\n"
        f"📤 Pending Withdraw: <b>{pending_withdraw}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih menu di bawah:",
        reply_markup=admin_menu_keyboard(pending_topup, pending_withdraw)
    )
    await callback.answer()
