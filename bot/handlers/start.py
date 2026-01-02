from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from prisma import Prisma
from prisma.models import User
from typing import Optional, Any

from bot.formatters.messages import format_welcome, format_terms, format_main_menu
from bot.keyboards.inline import get_terms_keyboard, get_main_menu_keyboard, CallbackData
from bot.utils.telegram_helpers import safe_edit_text
from bot.db.queries import get_user_by_telegram_id
from bot.config import config

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.bot.admin_ids


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    await state.clear()
    
    from_user = message.from_user
    if from_user is None:
        return
    
    if user:
        if user.status == "INACTIVE":
            await message.answer(
                "⚠️ <b>Akun Tidak Aktif</b>\n\n"
                "Akun Anda tidak aktif karena tidak ada aktivitas selama 6 bulan.\n"
                "Silakan daftar ulang untuk mengaktifkan kembali.",
                parse_mode="HTML"
            )
            await message.answer(
                format_welcome(),
                reply_markup=get_terms_keyboard(),
                parse_mode="HTML"
            )
            return
        
        if user.status == "BANNED":
            await message.answer(
                "🚫 <b>Akun Diblokir</b>\n\n"
                "Akun Anda telah diblokir. Hubungi support untuk informasi lebih lanjut.",
                parse_mode="HTML"
            )
            return
        
        if user.status == "PENDING":
            await message.answer(
                format_terms(),
                reply_markup=get_terms_keyboard(),
                parse_mode="HTML"
            )
            return
        
        fresh_user = await get_user_by_telegram_id(db, from_user.id)
        if not fresh_user:
            await message.answer(
                format_welcome(),
                reply_markup=get_terms_keyboard(),
                parse_mode="HTML"
            )
            return
        
        balance = fresh_user.balance.amount if fresh_user.balance else 0
        name = fresh_user.firstName or fresh_user.username or "User"
        
        await message.answer(
            format_main_menu(balance, name, from_user.id),
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(from_user.id)),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            format_welcome(),
            reply_markup=get_terms_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == CallbackData.BACK_MENU)
async def back_to_menu(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    await state.clear()
    
    if not user or user.status != "ACTIVE":
        await safe_edit_text(
            callback,
            format_welcome(),
            reply_markup=get_terms_keyboard()
        )
        await callback.answer()
        return
    
    fresh_user = await get_user_by_telegram_id(db, callback.from_user.id)
    if not fresh_user:
        await safe_edit_text(
            callback,
            format_welcome(),
            reply_markup=get_terms_keyboard()
        )
        await callback.answer()
        return
    
    balance = fresh_user.balance.amount if fresh_user.balance else 0
    name = fresh_user.firstName or fresh_user.username or "User"
    
    await safe_edit_text(
        callback,
        format_main_menu(balance, name, callback.from_user.id),
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(callback.from_user.id))
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.CANCEL_DELETE)
async def cancel_and_show_menu(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    await state.clear()
    
    from aiogram.types import Message as AiogramMessage
    msg = callback.message
    if isinstance(msg, AiogramMessage):
        try:
            await msg.delete()
        except Exception:
            pass
    
    if not user or user.status != "ACTIVE":
        if msg is not None and hasattr(msg, 'answer'):
            await msg.answer(
                format_welcome(),
                reply_markup=get_terms_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()
        return
    
    fresh_user = await get_user_by_telegram_id(db, callback.from_user.id)
    if not fresh_user:
        if msg is not None and hasattr(msg, 'answer'):
            await msg.answer(
                format_welcome(),
                reply_markup=get_terms_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()
        return
    
    balance = fresh_user.balance.amount if fresh_user.balance else 0
    name = fresh_user.firstName or fresh_user.username or "User"
    
    if msg is not None and hasattr(msg, 'answer'):
        await msg.answer(
            format_main_menu(balance, name, callback.from_user.id),
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(callback.from_user.id)),
            parse_mode="HTML"
        )
    await callback.answer()
