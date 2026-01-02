from decimal import Decimal
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional


class CallbackData:
    AGREE_TERMS = "signup:agree"
    SKIP_REFERRAL = "signup:skip_referral"
    
    MENU_BALANCE = "menu:balance"
    MENU_BUY = "menu:buy"
    MENU_SELL = "menu:sell"
    MENU_TOPUP = "menu:topup"
    MENU_WITHDRAW = "menu:withdraw"
    MENU_HISTORY = "menu:history"
    MENU_REFERRAL = "menu:referral"
    MENU_RATES = "menu:rates"
    MENU_HELP = "menu:help"
    MENU_PROFILE = "menu:profile"
    MENU_SETTINGS = "menu:settings"
    MENU_STOCK = "menu:stock"
    
    SETTINGS_SET_PIN = "settings:set_pin"
    SETTINGS_CHANGE_PIN = "settings:change_pin"
    SETTINGS_DELETE_PIN = "settings:delete_pin"
    
    BACK_MENU = "back:menu"
    BACK = "back"
    CANCEL = "cancel"
    CANCEL_DELETE = "cancel:delete_and_menu"


def get_terms_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Setuju & Daftar",
            callback_data=CallbackData.AGREE_TERMS
        )
    )
    return builder.as_markup()


def get_skip_referral_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Lewati",
            callback_data=CallbackData.SKIP_REFERRAL
        )
    )
    return builder.as_markup()


def get_location_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Bagikan Lokasi", request_location=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Bagikan Nomor HP", request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👛  Beli Crypto", callback_data=CallbackData.MENU_BUY),
        InlineKeyboardButton(text="🎈  Jual Crypto", callback_data=CallbackData.MENU_SELL),
    )
    builder.row(
        InlineKeyboardButton(text="➕  Deposit", callback_data=CallbackData.MENU_TOPUP),
        InlineKeyboardButton(text="➖  Withdraw", callback_data=CallbackData.MENU_WITHDRAW),
    )
    builder.row(
        InlineKeyboardButton(text="👀  Saldo", callback_data=CallbackData.MENU_BALANCE),
        InlineKeyboardButton(text="📊  Harga", callback_data=CallbackData.MENU_RATES),
    )
    builder.row(
        InlineKeyboardButton(text="📜  Riwayat", callback_data=CallbackData.MENU_HISTORY),
        InlineKeyboardButton(text="🎁  Referral", callback_data=CallbackData.MENU_REFERRAL),
    )
    builder.row(
        InlineKeyboardButton(text="👤  Profil", callback_data=CallbackData.MENU_PROFILE),
        InlineKeyboardButton(text="⚙️  Setting", callback_data=CallbackData.MENU_SETTINGS),
    )
    builder.row(
        InlineKeyboardButton(text="📦  Stock Crypto", callback_data=CallbackData.MENU_STOCK),
        InlineKeyboardButton(text="❓  Bantuan", callback_data=CallbackData.MENU_HELP),
    )
    return builder.as_markup()


def get_balance_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Deposit", callback_data=CallbackData.MENU_TOPUP),
        InlineKeyboardButton(text="➖ Withdraw", callback_data=CallbackData.MENU_WITHDRAW),
    )
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()


def get_coin_emoji(coin: str) -> str:
    emojis = {
        "BTC": "₿",
        "ETH": "Ξ",
        "BNB": "◈",
        "SOL": "◎",
        "USDT": "₮",
        "USDC": "◉",
    }
    return emojis.get(coin, "•")


def get_coins_keyboard(coins: list, action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for i in range(0, len(coins), 2):
        row = []
        for j in range(2):
            if i + j < len(coins):
                coin = coins[i + j]
                symbol = coin["symbol"] if isinstance(coin, dict) else coin
                emoji = get_coin_emoji(symbol)
                row.append(
                    InlineKeyboardButton(
                        text=f"{emoji} {symbol}",
                        callback_data=f"{action}:coin:{symbol}"
                    )
                )
        builder.row(*row)
    
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()


def get_networks_keyboard(networks: list[dict], coin: str, action: str, rate_idr: Optional[Decimal] = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for net in networks:
        network = net["network"]
        fee = net.get("withdraw_fee", Decimal("0"))
        
        if rate_idr and fee:
            fee_idr = Decimal(str(fee)) * rate_idr
            fee_text = f"Fee: Rp {fee_idr:,.0f}"
        else:
            fee_text = f"Fee: {fee} {coin}"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{network} ({fee_text})",
                callback_data=f"{action}:network:{coin}:{network}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=f"{action}:back"),
    )
    return builder.as_markup()


def get_confirm_keyboard(action: str, order_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Konfirmasi",
            callback_data=f"{action}:confirm:{order_id}"
        ),
        InlineKeyboardButton(
            text="❌ Batal",
            callback_data=f"{action}:cancel:{order_id}"
        ),
    )
    return builder.as_markup()


def get_topup_methods_keyboard(methods: list[dict], show_crypto: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if show_crypto:
        builder.row(
            InlineKeyboardButton(
                text="₿ Deposit Crypto",
                callback_data="topup:method:crypto"
            )
        )
    
    for method in methods:
        builder.row(
            InlineKeyboardButton(
                text=method['name'],
                callback_data=f"topup:method:{method['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()


def get_topup_confirm_keyboard(deposit_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Sudah Transfer",
            callback_data=f"topup:confirm:{deposit_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Batal",
            callback_data=f"topup:cancel:{deposit_id}"
        ),
    )
    return builder.as_markup()


def get_withdraw_methods_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Bank Transfer", callback_data="withdraw:method:bank"),
        InlineKeyboardButton(text="E-Wallet", callback_data="withdraw:method:ewallet"),
    )
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()


def get_ewallet_options_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    ewallets = ["GoPay", "OVO", "DANA", "ShopeePay", "LinkAja"]
    
    for i in range(0, len(ewallets), 2):
        row = []
        for j in range(2):
            if i + j < len(ewallets):
                ew = ewallets[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=ew,
                        callback_data=f"withdraw:ewallet:{ew}"
                    )
                )
        builder.row(*row)
    
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data="withdraw:back"),
    )
    return builder.as_markup()


def get_back_keyboard(callback_data: str = CallbackData.BACK_MENU) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=callback_data),
    )
    return builder.as_markup()


def get_settings_keyboard(has_pin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if has_pin:
        builder.row(
            InlineKeyboardButton(text="🔄 Ubah PIN", callback_data=CallbackData.SETTINGS_CHANGE_PIN),
        )
        builder.row(
            InlineKeyboardButton(text="🗑️ Hapus PIN", callback_data=CallbackData.SETTINGS_DELETE_PIN),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔐 Atur PIN", callback_data=CallbackData.SETTINGS_SET_PIN),
        )
    
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()


def get_referral_keyboard(ref_code: str, bot_username: str = "kriptoecerbot") -> InlineKeyboardMarkup:
    ref_link = f"https://t.me/{bot_username}?start={ref_code}"
    share_text = f"Yuk trading crypto bareng aku di @{bot_username}! Daftar pakai link ini: {ref_link}"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📤 Bagikan Link", url=share_url),
    )
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()


def get_cancel_keyboard(back_callback: str = CallbackData.CANCEL_DELETE) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Batal", callback_data=CallbackData.CANCEL_DELETE),
    )
    return builder.as_markup()


def get_history_pagination_keyboard(
    page: int,
    total_pages: int,
    tx_type: Optional[str] = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    filter_prefix = f":{tx_type}" if tx_type else ""
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Prev",
                callback_data=f"history:page{filter_prefix}:{page - 1}"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="history:current"
        )
    )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Next",
                callback_data=f"history:page{filter_prefix}:{page + 1}"
            )
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()
