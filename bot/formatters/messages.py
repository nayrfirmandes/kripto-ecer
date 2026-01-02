from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional
import random

WIB = timezone(timedelta(hours=7))

QUOTES = [
    "💰 Beli crypto (BTC, ETH, BNB, SOL, USDT, USDC) dengan harga kompetitif.",
    "📈 Jual crypto Anda dan dapatkan IDR langsung ke rekening.",
    "💳 Top up saldo melalui transfer bank dengan instan.",
    "💸 Withdraw ke rekening bank atau e-wallet favorit Anda.",
    "🎁 Ajak teman dan dapatkan bonus referral unlimited.",
    "⚡ Transaksi super cepat, konfirmasi dalam hitungan menit.",
    "🔒 Platform aman terpercaya dengan verifikasi multi-layer.",
    "📊 Pantau harga real-time untuk keputusan trading terbaik.",
]


def get_quote() -> str:
    return random.choice(QUOTES)


def get_wib_greeting() -> str:
    now = datetime.now(WIB)
    hour = now.hour
    if 5 <= hour < 11:
        return "Selamat pagi"
    elif 11 <= hour < 15:
        return "Selamat siang"
    elif 15 <= hour < 18:
        return "Selamat sore"
    else:
        return "Selamat malam"


def get_wib_time() -> datetime:
    return datetime.now(WIB)


def format_wib_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    wib_dt = dt.astimezone(WIB)
    return wib_dt.strftime("%d/%m/%Y %H:%M WIB")


class Emoji:
    CHECK = "✅"
    CROSS = "❌"
    ARROW = "→"
    DOT = "•"
    MONEY = "💰"
    COIN = "🪙"
    CHART = "📊"
    GIFT = "🎁"
    CLOCK = "⏳"
    WALLET = "💳"
    WARNING = "⚠️"
    INFO = "ℹ️"
    GEAR = "⚙️"
    LOCK = "🔐"
    HELP = "❓"


def format_currency(amount: Decimal, symbol: str = "IDR") -> str:
    if symbol == "IDR":
        return f"Rp {amount:,.0f}"
    return f"{amount:,.8f}".rstrip('0').rstrip('.') + f" {symbol}"


def format_welcome() -> str:
    return """<b>Selamat Datang di KriptoEcer</b> {coin}

Platform jual beli crypto terpercaya.
{dot} Transaksi cepat & aman
{dot} Harga kompetitif  
{dot} Support 24/7

Silakan daftar untuk mulai trading.""".format(coin=Emoji.COIN, dot=Emoji.DOT)


def format_terms() -> str:
    return """<b>Syarat & Ketentuan</b>

Dengan menggunakan layanan ini, Anda menyetujui:

1. Anda berusia minimal 18 tahun
2. Data yang diberikan adalah valid
3. Anda bertanggung jawab atas keamanan akun
4. Transaksi bersifat final setelah dikonfirmasi
5. Kami berhak membekukan akun yang mencurigakan

{warning} Pastikan Anda memahami risiko trading crypto.""".format(warning=Emoji.WARNING)


def format_main_menu(balance: Decimal | int, name: str, telegram_id: int) -> str:
    from bot.config import config
    greeting = get_wib_greeting()
    quote = get_quote()
    
    return """{greeting}, <b>{name}</b>!
<code>ID: {telegram_id}</code>

💰 Saldo: <b>{balance}</b>

<i>{quote}</i>

<i>⚠️ Pastikan menggunakan bot official @{bot_username}</i>""".format(
        greeting=greeting,
        name=name,
        telegram_id=telegram_id,
        balance=format_currency(balance),
        quote=quote,
        bot_username=config.bot.username
    )


def format_rates(rates: dict, usd_to_idr: Decimal) -> str:
    supported = ["BTC", "ETH", "BNB", "SOL", "USDT", "USDC"]
    
    lines = [f"{Emoji.CHART} <b>Harga Crypto Saat Ini</b>\n"]
    
    for symbol in supported:
        if symbol in rates:
            price_usd = Decimal(str(rates[symbol]))
            price_idr = price_usd * usd_to_idr
            lines.append(f"{Emoji.DOT} <b>{symbol}</b>: {format_currency(price_idr)}")
    
    lines.append(f"\n<i>Kurs saat ini: $1 = Rp {usd_to_idr:,.0f}</i>")
    lines.append(f"<i>Harga diperbarui secara real-time.</i>")
    
    return "\n".join(lines)


def format_balance(balance: Decimal) -> str:
    return """{money} <b>Saldo Anda</b>

<b>{balance}</b>

{dot} Deposit untuk menambah saldo
{dot} Withdraw untuk menarik saldo""".format(
        money=Emoji.MONEY,
        dot=Emoji.DOT,
        balance=format_currency(balance)
    )


def format_signup_email() -> str:
    return """<b>Email</b>

Masukkan alamat email Anda yang aktif.

<i>Contoh: nama@email.com</i>"""


def format_signup_whatsapp() -> str:
    return """<b>Nomor WhatsApp</b>

Masukkan nomor WhatsApp Anda.

<i>Contoh: 081234567890</i>"""


def format_signup_location() -> str:
    return """<b>Lokasi</b>

Bagikan lokasi Anda untuk verifikasi.
Klik tombol di bawah untuk share lokasi."""


def format_signup_referral() -> str:
    return """{gift} <b>Kode Referral</b> (Opsional)

Jika punya kode referral dari teman, masukkan sekarang.

Atau klik "Lewati" untuk lanjut.""".format(gift=Emoji.GIFT)


def format_signup_success(referral_code: str) -> str:
    return """{check} <b>Pendaftaran Berhasil!</b>

Akun Anda sudah aktif.

{gift} Kode referral: <code>{code}</code>
Bagikan ke teman untuk dapat bonus!""".format(
        check=Emoji.CHECK,
        gift=Emoji.GIFT,
        code=referral_code
    )


def format_buy_menu() -> str:
    return """{coin} <b>Beli Crypto</b>

Pilih cryptocurrency yang ingin Anda beli:""".format(coin=Emoji.COIN)


def format_sell_menu() -> str:
    return """{money} <b>Jual Crypto</b>

Pilih cryptocurrency yang ingin Anda jual:""".format(money=Emoji.MONEY)


def format_coin_networks(coin: str) -> str:
    return """<b>Pilih Network {coin}</b>

Pilih network yang ingin Anda gunakan:""".format(coin=coin)


def format_buy_amount(coin: str, network: str, rate: Decimal, margin: Decimal) -> str:
    final_rate = rate * (1 + margin / 100)
    return """{coin_emoji} <b>Beli {coin}</b> ({network})

{chart} Rate: <b>{rate}</b> / {coin}
<i>Harga sudah termasuk margin {margin}%</i>

Masukkan jumlah pembelian dalam Rupiah:
<i>Minimal pembelian: Rp 10.000</i>""".format(
        coin_emoji=Emoji.COIN,
        chart=Emoji.CHART,
        coin=coin,
        network=network,
        rate=format_currency(final_rate),
        margin=margin
    )


def format_buy_confirm(
    coin: str,
    network: str,
    fiat_amount: Decimal,
    crypto_amount: Decimal,
    rate: Decimal,
    network_fee: Decimal,
    total: Decimal
) -> str:
    return """{coin_emoji} <b>Konfirmasi Pembelian Crypto</b>

{dot} Coin: <b>{coin}</b> ({network})
{dot} Jumlah: <b>{fiat}</b>
{dot} Rate: <b>{rate}</b>/{coin}
{dot} Network Fee: <b>{fee}</b>

{arrow} Anda akan menerima: <b>{crypto}</b>
{arrow} Dipotong dari saldo: <b>{total}</b>

Apakah Anda ingin melanjutkan pembelian?""".format(
        coin_emoji=Emoji.COIN,
        dot=Emoji.DOT,
        arrow=Emoji.ARROW,
        coin=coin,
        network=network,
        fiat=format_currency(fiat_amount),
        rate=format_currency(rate),
        fee=format_currency(network_fee, coin),
        crypto=format_currency(crypto_amount, coin),
        total=format_currency(total)
    )


def format_sell_confirm(
    coin: str,
    network: str,
    crypto_amount: Decimal,
    fiat_amount: Decimal,
    rate: Decimal,
    deposit_address: str
) -> str:
    return """{money} <b>Konfirmasi Penjualan Crypto</b>

{dot} Coin: <b>{coin}</b> ({network})
{dot} Jumlah: <b>{crypto}</b>
{dot} Rate: <b>{rate}</b>/{coin}

{arrow} Saldo Anda akan bertambah: <b>{fiat}</b>

Silakan kirim <b>{crypto}</b> ke alamat:
<code>{address}</code>

{warning} <i>Pastikan menggunakan network: {network}</i>""".format(
        money=Emoji.MONEY,
        dot=Emoji.DOT,
        arrow=Emoji.ARROW,
        warning=Emoji.WARNING,
        coin=coin,
        network=network,
        crypto=format_currency(crypto_amount, coin),
        rate=format_currency(rate),
        fiat=format_currency(fiat_amount),
        address=deposit_address
    )


def format_topup_menu() -> str:
    return """{wallet} <b>Deposit Saldo</b>

Pilih metode pembayaran yang tersedia:""".format(wallet=Emoji.WALLET)


def format_topup_amount(method: str) -> str:
    return """{wallet} <b>Deposit via {method}</b>

Masukkan jumlah deposit dalam Rupiah:
<i>Minimal deposit: Rp 10.000</i>""".format(wallet=Emoji.WALLET, method=method)


def format_topup_instruction(
    method: str,
    account_no: str,
    account_name: str,
    amount: Decimal
) -> str:
    return """{wallet} <b>Instruksi Pembayaran</b>

Transfer ke:
{dot} <b>{method}</b>
{dot} No. Rek: <code>{account_no}</code>
{dot} Nama: <b>{account_name}</b>
{dot} Jumlah: <b>{amount}</b>

{warning} <i>Transfer dengan jumlah TEPAT</i>""".format(
        wallet=Emoji.WALLET,
        dot=Emoji.DOT,
        warning=Emoji.WARNING,
        method=method,
        account_no=account_no,
        account_name=account_name,
        amount=format_currency(amount)
    )


def format_withdraw_menu() -> str:
    return """{money} <b>Withdraw Saldo</b>

Pilih metode penarikan yang tersedia:""".format(money=Emoji.MONEY)


def format_transaction_success(tx_type: str, amount: Decimal) -> str:
    return """{check} <b>Transaksi Berhasil!</b>

{tx_type}: <b>{amount}</b>
Terima kasih telah menggunakan layanan kami.""".format(
        check=Emoji.CHECK,
        tx_type=tx_type,
        amount=format_currency(amount)
    )


def format_transaction_pending() -> str:
    return """{clock} <b>Menunggu Konfirmasi</b>

Transaksi sedang diproses.
Anda akan menerima notifikasi setelah dikonfirmasi.""".format(clock=Emoji.CLOCK)


def format_error(message: str) -> str:
    return """{cross} <b>Terjadi Kesalahan</b>

{message}""".format(cross=Emoji.CROSS, message=message)


def format_insufficient_balance(required: Decimal, current: Decimal) -> str:
    return """{warning} <b>Saldo Tidak Cukup</b>

Dibutuhkan: <b>{required}</b>
Saldo Anda: <b>{current}</b>

Silakan deposit terlebih dahulu.""".format(
        warning=Emoji.WARNING,
        required=format_currency(required),
        current=format_currency(current)
    )


def format_history_item(
    tx_type: str,
    amount: Decimal,
    status: str,
    created_at: str,
    coin: Optional[str] = None
) -> str:
    status_symbol = {
        "PENDING": "○",
        "PROCESSING": "◐",
        "COMPLETED": Emoji.CHECK,
        "FAILED": Emoji.CROSS,
        "CANCELLED": Emoji.CROSS,
    }.get(status, "○")
    
    coin_str = f" ({coin})" if coin else ""
    
    return f"{status_symbol} {tx_type}{coin_str}: {format_currency(amount)} - {created_at}"


def format_referral_info(code: str, count: int, bonus_earned: Decimal, bot_username: str = "") -> str:
    if not bot_username:
        from bot.config import config
        bot_username = config.bot.username
    ref_link = f"https://t.me/{bot_username}?start={code}"
    return """{gift} <b>Program Referral Anda</b>

{dot} Kode Referral: <code>{code}</code>
{dot} Total Undangan: <b>{count} orang</b>
{money} Total Bonus: <b>{bonus}</b>

{link} <b>Link Referral:</b>
<code>{ref_link}</code>

Bagikan link di atas kepada teman Anda.
Dapatkan bonus setiap ada yang mendaftar!""".format(
        gift=Emoji.GIFT,
        dot=Emoji.DOT,
        money=Emoji.MONEY,
        link=Emoji.ARROW,
        code=code,
        count=count,
        bonus=format_currency(bonus_earned),
        ref_link=ref_link
    )


def format_profile(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    email: Optional[str],
    whatsapp: Optional[str],
    status: str,
    referral_code: str,
    created_at,
    balance: Decimal | int
) -> str:
    status_text = {
        "ACTIVE": f"{Emoji.CHECK} Aktif",
        "PENDING": "○ Pending",
        "INACTIVE": f"{Emoji.WARNING} Tidak Aktif",
        "BANNED": f"{Emoji.CROSS} Diblokir",
    }.get(status, status)
    
    created_wib = format_wib_datetime(created_at) if created_at else "-"
    
    return """<b>Profil Saya</b>

{dot} <b>Nama:</b> {name}
{dot} <b>Username:</b> @{username}
{dot} <b>ID:</b> <code>{telegram_id}</code>
{dot} <b>Email:</b> {email}
{dot} <b>WhatsApp:</b> {whatsapp}

{money} <b>Saldo:</b> {balance}
{gift} <b>Kode Referral:</b> <code>{referral_code}</code>

<b>Status Akun:</b> {status}
<b>Terdaftar:</b> {created_at}""".format(
        dot=Emoji.DOT,
        money=Emoji.MONEY,
        gift=Emoji.GIFT,
        name=first_name or "-",
        username=username or "-",
        telegram_id=telegram_id,
        email=email or "-",
        whatsapp=whatsapp or "-",
        balance=format_currency(balance),
        referral_code=referral_code,
        status=status_text,
        created_at=created_wib
    )
