from decimal import Decimal, InvalidOperation
from typing import Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from prisma import Prisma

from bot.formatters.messages import Emoji
from bot.utils.telegram_helpers import get_callback_data
from bot.keyboards.admin import referral_settings_keyboard, referral_create_keyboard, cancel_keyboard
from bot.handlers.admin.shared import AdminStates, is_admin, safe_edit_text

router = Router()


@router.callback_query(F.data == "admin:referral")
async def admin_referral(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    setting = await db.referralsetting.find_first(where={"isActive": True})
    
    if setting:
        text = (
            "<b>Referral Settings</b>\n\n"
            f"Bonus Referrer: <b>Rp {setting.referrerBonus:,.0f}</b>\n"
            f"Bonus Referee: <b>Rp {setting.refereeBonus:,.0f}</b>\n"
            f"Status: <b>{'Active' if setting.isActive else 'Inactive'}</b>\n"
        )
        await safe_edit_text(callback, text, reply_markup=referral_settings_keyboard(setting.id))
    else:
        text = (
            "<b>Referral Settings</b>\n\n"
            "Belum ada setting referral. Buat baru?"
        )
        await safe_edit_text(callback, text, reply_markup=referral_create_keyboard())
    
    await callback.answer()


@router.callback_query(F.data == "admin:create_referral")
async def create_referral_setting(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    await db.referralsetting.create(
        data={
            "referrerBonus": Decimal("10000"),
            "refereeBonus": Decimal("5000"),
            "isActive": True,
        }
    )
    
    await callback.answer("Referral setting berhasil dibuat!", show_alert=True)
    await admin_referral(callback, db)


@router.callback_query(F.data.startswith("admin:set_referrer_bonus:"))
async def set_referrer_bonus_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    setting_id = get_callback_data(callback).split(":")[-1]
    setting = await db.referralsetting.find_unique(where={"id": setting_id})
    
    if not setting:
        await callback.answer("Setting tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_referrer_bonus)
    await state.update_data(setting_id=setting_id)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Bonus Referrer</b>\n\n"
        f"Current: <b>Rp {setting.referrerBonus:,.0f}</b>\n\n"
        f"Masukkan nilai bonus baru (contoh: 10000):",
        reply_markup=cancel_keyboard("admin:referral")
    )
    await callback.answer()


@router.message(AdminStates.editing_referrer_bonus)
async def set_referrer_bonus_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    setting_id = data.get("setting_id")
    if not isinstance(setting_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        bonus = Decimal(message.text or "0").quantize(Decimal("1"))
        if bonus < 0:
            await message.answer("Bonus tidak boleh negatif")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 10000)")
        return
    
    await db.referralsetting.update(where={"id": setting_id}, data={"referrerBonus": bonus})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Bonus referrer berhasil diubah ke Rp {bonus:,.0f}")


@router.callback_query(F.data.startswith("admin:set_referee_bonus:"))
async def set_referee_bonus_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    setting_id = get_callback_data(callback).split(":")[-1]
    setting = await db.referralsetting.find_unique(where={"id": setting_id})
    
    if not setting:
        await callback.answer("Setting tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_referee_bonus)
    await state.update_data(setting_id=setting_id)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Bonus Referee</b>\n\n"
        f"Current: <b>Rp {setting.refereeBonus:,.0f}</b>\n\n"
        f"Masukkan nilai bonus baru (contoh: 5000):",
        reply_markup=cancel_keyboard("admin:referral")
    )
    await callback.answer()


@router.message(AdminStates.editing_referee_bonus)
async def set_referee_bonus_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    setting_id = data.get("setting_id")
    if not isinstance(setting_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        bonus = Decimal(message.text or "0").quantize(Decimal("1"))
        if bonus < 0:
            await message.answer("Bonus tidak boleh negatif")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 5000)")
        return
    
    await db.referralsetting.update(where={"id": setting_id}, data={"refereeBonus": bonus})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Bonus referee berhasil diubah ke Rp {bonus:,.0f}")
