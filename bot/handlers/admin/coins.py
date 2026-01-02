from decimal import Decimal, InvalidOperation
from typing import Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from prisma import Prisma

from bot.formatters.messages import Emoji
from bot.utils.telegram_helpers import get_callback_data
from bot.keyboards.admin import coin_list_keyboard, coin_networks_keyboard, coin_edit_keyboard, cancel_keyboard
from bot.handlers.admin.shared import AdminStates, is_admin, safe_edit_text

router = Router()


@router.callback_query(F.data == "admin:coins")
async def admin_coins(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coins = await db.coinsetting.find_many(order={"coinSymbol": "asc"})
    
    coin_map: dict[str, bool] = {}
    for coin in coins:
        if coin.coinSymbol not in coin_map:
            coin_map[coin.coinSymbol] = coin.isActive
        elif coin.isActive:
            coin_map[coin.coinSymbol] = True
    
    text = "<b>🪙 Coin Settings</b>\n\n"
    coin_list: list[tuple[str, bool]] = []
    
    for symbol, is_active in sorted(coin_map.items()):
        status = "🟢 Active" if is_active else "🔴 Inactive"
        text += f"{symbol}: {status}\n"
        coin_list.append((symbol, is_active))
    
    await safe_edit_text(callback, text, reply_markup=coin_list_keyboard(coin_list))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:coin:"))
async def admin_coin_detail(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    symbol = parts[2]
    
    coins = await db.coinsetting.find_many(
        where={"coinSymbol": symbol},
        order={"network": "asc"}
    )
    
    text = f"<b>{symbol} Networks</b>\n\n"
    networks: list[tuple[str, str, bool]] = []
    
    for coin in coins:
        status = "ON" if coin.isActive else "OFF"
        text += (
            f"<b>{coin.network}</b> - {status}\n"
            f"  Buy: {coin.buyMargin}% | Sell: {coin.sellMargin}%\n"
            f"  Min: Rp {coin.minBuy:,.0f} - Max: Rp {coin.maxBuy:,.0f}\n\n"
        )
        networks.append((coin.id, coin.network, coin.isActive))
    
    await safe_edit_text(callback, text, reply_markup=coin_networks_keyboard(symbol, networks))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:toggle_coin:"))
async def toggle_coin(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    coin_id = parts[2]
    
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await db.coinsetting.update(
        where={"id": coin_id},
        data={"isActive": not coin.isActive}
    )
    
    status = "disabled" if coin.isActive else "enabled"
    await callback.answer(f"{coin.coinSymbol} {coin.network} {status}!", show_alert=True)
    
    new_callback_data = f"admin:coin:{coin.coinSymbol}"
    original_data = callback.data
    callback.data = new_callback_data
    await admin_coin_detail(callback, db)
    callback.data = original_data


@router.callback_query(F.data.startswith("admin:edit_coin:"))
async def edit_coin_menu(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    coin_id = parts[2]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    text = (
        f"<b>Edit {coin.coinSymbol} - {coin.network}</b>\n\n"
        f"Buy Margin: <b>{coin.buyMargin}%</b>\n"
        f"Sell Margin: <b>{coin.sellMargin}%</b>\n"
        f"Min Buy: <b>Rp {coin.minBuy:,.0f}</b>\n"
        f"Max Buy: <b>Rp {coin.maxBuy:,.0f}</b>\n"
        f"Min Sell: <b>Rp {coin.minSell:,.0f}</b>\n"
        f"Max Sell: <b>Rp {coin.maxSell:,.0f}</b>\n"
    )
    
    await safe_edit_text(callback, text, reply_markup=coin_edit_keyboard(coin_id, coin.coinSymbol))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:set_buy_margin:"))
async def set_buy_margin_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coin_id = get_callback_data(callback).split(":")[-1]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_buy_margin)
    await state.update_data(coin_id=coin_id, coin_symbol=coin.coinSymbol)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Buy Margin - {coin.coinSymbol} {coin.network}</b>\n\n"
        f"Current: <b>{coin.buyMargin}%</b>\n\n"
        f"Masukkan nilai margin baru (contoh: 2.5):",
        reply_markup=cancel_keyboard(f"admin:edit_coin:{coin_id}")
    )
    await callback.answer()


@router.message(AdminStates.editing_buy_margin)
async def set_buy_margin_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    coin_id = data.get("coin_id")
    if not isinstance(coin_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        margin = Decimal(message.text or "0").quantize(Decimal("0.01"))
        if margin < 0 or margin > 100:
            await message.answer("Margin harus antara 0-100%")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 2.5)")
        return
    
    await db.coinsetting.update(where={"id": coin_id}, data={"buyMargin": margin})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Buy margin berhasil diubah ke {margin}%")


@router.callback_query(F.data.startswith("admin:set_sell_margin:"))
async def set_sell_margin_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coin_id = get_callback_data(callback).split(":")[-1]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_sell_margin)
    await state.update_data(coin_id=coin_id, coin_symbol=coin.coinSymbol)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Sell Margin - {coin.coinSymbol} {coin.network}</b>\n\n"
        f"Current: <b>{coin.sellMargin}%</b>\n\n"
        f"Masukkan nilai margin baru (contoh: 2.5):",
        reply_markup=cancel_keyboard(f"admin:edit_coin:{coin_id}")
    )
    await callback.answer()


@router.message(AdminStates.editing_sell_margin)
async def set_sell_margin_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    coin_id = data.get("coin_id")
    if not isinstance(coin_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        margin = Decimal(message.text or "0").quantize(Decimal("0.01"))
        if margin < 0 or margin > 100:
            await message.answer("Margin harus antara 0-100%")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 2.5)")
        return
    
    await db.coinsetting.update(where={"id": coin_id}, data={"sellMargin": margin})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Sell margin berhasil diubah ke {margin}%")


@router.callback_query(F.data.startswith("admin:set_min_buy:"))
async def set_min_buy_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coin_id = get_callback_data(callback).split(":")[-1]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_min_buy)
    await state.update_data(coin_id=coin_id)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Min Buy - {coin.coinSymbol} {coin.network}</b>\n\n"
        f"Current: <b>Rp {coin.minBuy:,.0f}</b>\n\n"
        f"Masukkan nilai minimum (contoh: 50000):",
        reply_markup=cancel_keyboard(f"admin:edit_coin:{coin_id}")
    )
    await callback.answer()


@router.message(AdminStates.editing_min_buy)
async def set_min_buy_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    coin_id = data.get("coin_id")
    if not isinstance(coin_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        amount = Decimal(message.text or "0").quantize(Decimal("1"))
        if amount < 0:
            await message.answer("Nilai tidak boleh negatif")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 50000)")
        return
    
    await db.coinsetting.update(where={"id": coin_id}, data={"minBuy": amount})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Min buy berhasil diubah ke Rp {amount:,.0f}")


@router.callback_query(F.data.startswith("admin:set_max_buy:"))
async def set_max_buy_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coin_id = get_callback_data(callback).split(":")[-1]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_max_buy)
    await state.update_data(coin_id=coin_id)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Max Buy - {coin.coinSymbol} {coin.network}</b>\n\n"
        f"Current: <b>Rp {coin.maxBuy:,.0f}</b>\n\n"
        f"Masukkan nilai maximum (contoh: 50000000):",
        reply_markup=cancel_keyboard(f"admin:edit_coin:{coin_id}")
    )
    await callback.answer()


@router.message(AdminStates.editing_max_buy)
async def set_max_buy_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    coin_id = data.get("coin_id")
    if not isinstance(coin_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        amount = Decimal(message.text or "0").quantize(Decimal("1"))
        if amount < 0:
            await message.answer("Nilai tidak boleh negatif")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 50000000)")
        return
    
    await db.coinsetting.update(where={"id": coin_id}, data={"maxBuy": amount})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Max buy berhasil diubah ke Rp {amount:,.0f}")


@router.callback_query(F.data.startswith("admin:set_min_sell:"))
async def set_min_sell_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coin_id = get_callback_data(callback).split(":")[-1]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_min_sell)
    await state.update_data(coin_id=coin_id)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Min Sell - {coin.coinSymbol} {coin.network}</b>\n\n"
        f"Current: <b>Rp {coin.minSell:,.0f}</b>\n\n"
        f"Masukkan nilai minimum (contoh: 50000):",
        reply_markup=cancel_keyboard(f"admin:edit_coin:{coin_id}")
    )
    await callback.answer()


@router.message(AdminStates.editing_min_sell)
async def set_min_sell_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    coin_id = data.get("coin_id")
    if not isinstance(coin_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        amount = Decimal(message.text or "0").quantize(Decimal("1"))
        if amount < 0:
            await message.answer("Nilai tidak boleh negatif")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 50000)")
        return
    
    await db.coinsetting.update(where={"id": coin_id}, data={"minSell": amount})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Min sell berhasil diubah ke Rp {amount:,.0f}")


@router.callback_query(F.data.startswith("admin:set_max_sell:"))
async def set_max_sell_start(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coin_id = get_callback_data(callback).split(":")[-1]
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await state.set_state(AdminStates.editing_max_sell)
    await state.update_data(coin_id=coin_id)
    
    await safe_edit_text(
        callback,
        f"<b>Edit Max Sell - {coin.coinSymbol} {coin.network}</b>\n\n"
        f"Current: <b>Rp {coin.maxSell:,.0f}</b>\n\n"
        f"Masukkan nilai maximum (contoh: 50000000):",
        reply_markup=cancel_keyboard(f"admin:edit_coin:{coin_id}")
    )
    await callback.answer()


@router.message(AdminStates.editing_max_sell)
async def set_max_sell_finish(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    data = await state.get_data()
    coin_id = data.get("coin_id")
    if not isinstance(coin_id, str):
        await state.clear()
        await message.answer("Session expired. Silakan coba lagi.")
        return
    
    try:
        amount = Decimal(message.text or "0").quantize(Decimal("1"))
        if amount < 0:
            await message.answer("Nilai tidak boleh negatif")
            return
    except InvalidOperation:
        await message.answer("Format tidak valid. Masukkan angka (contoh: 50000000)")
        return
    
    await db.coinsetting.update(where={"id": coin_id}, data={"maxSell": amount})
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Max sell berhasil diubah ke Rp {amount:,.0f}")
