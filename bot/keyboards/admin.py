from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_keyboard(pending_topup: int = 0, pending_withdraw: int = 0) -> InlineKeyboardMarkup:
    topup_text = f"📥 Topup ({pending_topup})" if pending_topup > 0 else "📥 Topup"
    withdraw_text = f"📤 Withdraw ({pending_withdraw})" if pending_withdraw > 0 else "📤 Withdraw"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Dashboard", callback_data="admin:dashboard"),
        ],
        [
            InlineKeyboardButton(text=topup_text, callback_data="admin:pending_topup"),
            InlineKeyboardButton(text=withdraw_text, callback_data="admin:pending_withdraw"),
        ],
        [
            InlineKeyboardButton(text="🪙 Coins", callback_data="admin:coins"),
            InlineKeyboardButton(text="💳 Payments", callback_data="admin:payments"),
        ],
        [
            InlineKeyboardButton(text="🎁 Referral", callback_data="admin:referral"),
            InlineKeyboardButton(text="👥 Users", callback_data="admin:users"),
        ],
        [
            InlineKeyboardButton(text="← Menu Utama", callback_data="back:menu"),
        ],
    ])


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Back", callback_data="admin:menu")]
    ])


def coin_list_keyboard(coins: list[tuple[str, bool]]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for symbol, is_active in coins:
        status = "🟢" if is_active else "🔴"
        buttons.append([
            InlineKeyboardButton(text=f"{status} {symbol}", callback_data=f"admin:coin:{symbol}")
        ])
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def coin_networks_keyboard(coin_symbol: str, networks: list[tuple[str, str, bool]]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for coin_id, network, is_active in networks:
        toggle_text = "OFF" if is_active else "ON"
        buttons.append([
            InlineKeyboardButton(text=f"{network}: {toggle_text}", callback_data=f"admin:toggle_coin:{coin_id}"),
            InlineKeyboardButton(text="Edit", callback_data=f"admin:edit_coin:{coin_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="admin:coins")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def coin_edit_keyboard(coin_id: str, coin_symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Edit Buy Margin", callback_data=f"admin:set_buy_margin:{coin_id}"),
            InlineKeyboardButton(text="Edit Sell Margin", callback_data=f"admin:set_sell_margin:{coin_id}"),
        ],
        [
            InlineKeyboardButton(text="Edit Min Buy", callback_data=f"admin:set_min_buy:{coin_id}"),
            InlineKeyboardButton(text="Edit Max Buy", callback_data=f"admin:set_max_buy:{coin_id}"),
        ],
        [
            InlineKeyboardButton(text="Edit Min Sell", callback_data=f"admin:set_min_sell:{coin_id}"),
            InlineKeyboardButton(text="Edit Max Sell", callback_data=f"admin:set_max_sell:{coin_id}"),
        ],
        [InlineKeyboardButton(text="← Back", callback_data=f"admin:coin:{coin_symbol}")],
    ])


def cancel_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cancel", callback_data=callback_data)]
    ])


def payment_list_keyboard(payments: list[tuple[str, str, bool]]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for payment_id, name, is_active in payments:
        toggle_text = "Disable" if is_active else "Enable"
        buttons.append([
            InlineKeyboardButton(text=f"{name}: {toggle_text}", callback_data=f"admin:toggle_payment:{payment_id}")
        ])
    buttons.append([InlineKeyboardButton(text="➕ Tambah Payment", callback_data="admin:add_payment")])
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bank Transfer", callback_data="payment_type:BANK")],
        [InlineKeyboardButton(text="E-Wallet", callback_data="payment_type:EWALLET")],
        [InlineKeyboardButton(text="Cancel", callback_data="admin:payments")],
    ])


def referral_settings_keyboard(setting_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Edit Bonus Referrer", callback_data=f"admin:set_referrer_bonus:{setting_id}")],
        [InlineKeyboardButton(text="Edit Bonus Referee", callback_data=f"admin:set_referee_bonus:{setting_id}")],
        [InlineKeyboardButton(text="← Back", callback_data="admin:menu")],
    ])


def referral_create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Buat Setting", callback_data="admin:create_referral")],
        [InlineKeyboardButton(text="← Back", callback_data="admin:menu")],
    ])


def topup_action_keyboard(deposit_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin:approve_topup:{deposit_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin:reject_topup:{deposit_id}"),
        ]
    ])


def withdraw_action_keyboard(withdrawal_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin:approve_withdraw:{withdrawal_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin:reject_withdraw:{withdrawal_id}"),
        ]
    ])
