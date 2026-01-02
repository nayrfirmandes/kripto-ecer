import hashlib
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma
from typing import Optional

from bot.formatters.messages import Emoji
from bot.keyboards.inline import CallbackData, get_settings_keyboard, get_back_keyboard, get_cancel_keyboard

router = Router()


class PinStates(StatesGroup):
    waiting_current_pin = State()
    waiting_new_pin = State()
    waiting_confirm_pin = State()
    confirming_delete_pin = State()


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin: str, pin_hash: str) -> bool:
    return hash_pin(pin) == pin_hash


@router.callback_query(F.data == CallbackData.MENU_SETTINGS)
async def show_settings(callback: CallbackQuery, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user:
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    fresh_user = await db.user.find_unique(
        where={"id": user.id}
    )
    
    has_pin = bool(fresh_user.pinHash) if fresh_user else False
    pin_status = f"{Emoji.CHECK} PIN sudah diatur" if has_pin else f"{Emoji.WARNING} PIN belum diatur"
    
    settings_text = f"""{Emoji.GEAR} <b>Pengaturan Akun</b>

{Emoji.DOT} <b>PIN Transaksi:</b> {pin_status}

PIN digunakan untuk mengamankan transaksi Anda.
Pastikan PIN tidak diketahui orang lain."""
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_settings_keyboard(has_pin),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.SETTINGS_SET_PIN)
async def start_set_pin(callback: CallbackQuery, state: FSMContext, **kwargs):
    await state.set_state(PinStates.waiting_new_pin)
    
    await callback.message.edit_text(
        f"""{Emoji.LOCK} <b>Atur PIN Transaksi</b>

Masukkan PIN 6 digit untuk mengamankan transaksi.

<i>PIN harus berupa 6 angka.</i>""",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.SETTINGS_CHANGE_PIN)
async def start_change_pin(callback: CallbackQuery, state: FSMContext, **kwargs):
    await state.set_state(PinStates.waiting_current_pin)
    await state.update_data(action="change")
    
    await callback.message.edit_text(
        f"""{Emoji.LOCK} <b>Ubah PIN Transaksi</b>

Masukkan PIN lama Anda untuk verifikasi.

<i>Masukkan 6 digit PIN lama.</i>""",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.SETTINGS_DELETE_PIN)
async def confirm_delete_pin(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Ask for PIN confirmation before deleting"""
    await state.set_state(PinStates.waiting_current_pin)
    await state.update_data(action="delete")
    
    await callback.message.edit_text(
        f"""{Emoji.LOCK} <b>Hapus PIN Transaksi</b>

Masukkan PIN Anda untuk verifikasi sebelum dihapus.

<i>Masukkan 6 digit PIN.</i>""",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PinStates.waiting_current_pin)
async def process_current_pin(message: Message, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    await message.delete()
    
    if not user:
        await state.clear()
        return
    
    pin = message.text.strip()
    
    if not pin.isdigit() or len(pin) != 6:
        await message.answer(
            f"{Emoji.CROSS} PIN harus berupa 6 digit angka.\n\nSilakan masukkan PIN yang benar.",
            parse_mode="HTML"
        )
        return
    
    if not verify_pin(pin, user.pinHash):
        await message.answer(
            f"{Emoji.CROSS} PIN tidak sesuai.\n\nSilakan masukkan PIN yang benar.",
            parse_mode="HTML"
        )
        return
    
    # Check what action user wants to do
    data = await state.get_data()
    action = data.get("action", "change")
    
    if action == "delete":
        # Directly delete PIN
        await db.user.update(
            where={"id": user.id},
            data={"pinHash": None}
        )
        
        await state.clear()
        
        await message.answer(
            f"""{Emoji.CHECK} <b>PIN Berhasil Dihapus!</b>

PIN transaksi Anda sudah dihapus.
Anda dapat mengatur PIN baru kapan saja di menu pengaturan.""",
            reply_markup=get_settings_back_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Change PIN flow
        await state.set_state(PinStates.waiting_new_pin)
        await message.answer(
            f"""{Emoji.CHECK} PIN lama berhasil diverifikasi.

Sekarang masukkan PIN baru Anda.
<i>PIN harus berupa 6 angka.</i>""",
            parse_mode="HTML"
        )


@router.message(PinStates.waiting_new_pin)
async def process_new_pin(message: Message, state: FSMContext, **kwargs):
    await message.delete()
    
    pin = message.text.strip()
    
    if not pin.isdigit() or len(pin) != 6:
        await message.answer(
            f"{Emoji.CROSS} PIN harus berupa 6 digit angka.\n\nSilakan masukkan PIN yang valid.",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(new_pin=pin)
    await state.set_state(PinStates.waiting_confirm_pin)
    
    await message.answer(
        f"""{Emoji.CHECK} PIN diterima.

Masukkan ulang PIN yang sama untuk konfirmasi.""",
        parse_mode="HTML"
    )


@router.message(PinStates.waiting_confirm_pin)
async def process_confirm_pin(message: Message, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    await message.delete()
    
    if not user:
        await state.clear()
        return
    
    data = await state.get_data()
    new_pin = data.get("new_pin")
    confirm_pin = message.text.strip()
    
    if confirm_pin != new_pin:
        await message.answer(
            f"{Emoji.CROSS} PIN tidak cocok.\n\nSilakan masukkan ulang PIN yang sama.",
            parse_mode="HTML"
        )
        return
    
    pin_hash = hash_pin(new_pin)
    await db.user.update(
        where={"id": user.id},
        data={"pinHash": pin_hash}
    )
    
    await state.clear()
    
    await message.answer(
        f"""{Emoji.CHECK} <b>PIN Berhasil Diatur!</b>

PIN transaksi Anda sudah aktif dan siap digunakan.
Jangan bagikan PIN kepada siapapun.""",
        reply_markup=get_settings_back_keyboard(),
        parse_mode="HTML"
    )


def get_settings_back_keyboard():
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="← Kembali ke Pengaturan", callback_data=CallbackData.MENU_SETTINGS),
    )
    builder.row(
        InlineKeyboardButton(text="← Menu Utama", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()
