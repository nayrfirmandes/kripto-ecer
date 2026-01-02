# Crypto Trading Telegram Bot

## Overview
Telegram bot untuk jual beli cryptocurrency dengan sistem saldo internal. Bot ini terintegrasi dengan OxaPay untuk transaksi crypto.

## Tech Stack
- **Bot**: Python 3.11 + Aiogram 3.x
- **Database**: PostgreSQL (NeonSQL)
- **ORM**: Prisma
- **Admin Panel**: Telegram inline keyboard (built-in)

## Project Structure
```
bot/
├── main.py              # Entry point
├── config.py            # Environment config
├── webhook.py           # OxaPay webhook handler
├── handlers/            # Telegram handlers
│   ├── start.py         # /start command
│   ├── signup.py        # Registration flow
│   ├── menu.py          # Main menu
│   ├── balance.py       # Balance view
│   ├── topup.py         # Top up flow
│   ├── withdraw.py      # Withdraw flow
│   ├── buy.py           # Buy crypto flow
│   ├── sell.py          # Sell crypto flow
│   ├── history.py       # Transaction history
│   └── admin.py         # Admin commands
├── services/            # Business logic
│   └── oxapay.py        # OxaPay API wrapper
├── keyboards/           # InlineKeyboard builders
│   └── inline.py        # All keyboards
├── formatters/          # Message formatters + emoji
│   └── messages.py      # All messages
├── middlewares/         # Aiogram middlewares
│   ├── throttling.py    # Rate limiting
│   ├── database.py      # DB injection
│   ├── user_status.py   # User status check
│   └── logging.py       # Request logging
├── db/                  # Database queries
│   └── queries.py       # All DB operations
└── utils/               # Helpers
    └── helpers.py       # Utility functions

prisma/
└── schema.prisma        # Database schema

pyrightconfig.json       # Pyright type checking config
```

## Environment Variables
Required secrets:
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `BOT_DATABASE` - NeonSQL connection string
- `OXAPAY_MERCHANT_API_KEY` - OxaPay merchant API key
- `OXAPAY_PAYOUT_API_KEY` - OxaPay payout API key
- `OXAPAY_WEBHOOK_SECRET` - Webhook verification secret
- `ADMIN_TELEGRAM_IDS` - Comma-separated admin Telegram IDs

Optional config (via environment variables):
- `BOT_USERNAME` - Bot username without @ (default: kriptoecerbot)
- `USD_TO_IDR` - USD to IDR exchange rate (default: 16000)
- `WEBHOOK_HOST` - Webhook host domain

## Features
- User registration with email, WhatsApp, location
- Referral system with bonus
- Balance management (top up, withdraw)
- Buy crypto (BTC, ETH, BNB, SOL, USDT, USDC)
- Sell crypto with deposit address
- Transaction history
- Admin commands for approving transactions
- Rate limiting (100-300ms response time target)
- User inactive detection (6 months)

## Running the Bot
```bash
python run_bot.py
```

## Database Commands
```bash
# Generate Prisma client
prisma generate

# Push schema to database
prisma db push

# Open Prisma Studio
prisma studio
```

## Admin Panel (via Telegram)
Admin panel diakses langsung dari Telegram dengan command `/admin`. Fitur:
- Dashboard (stats users, pending transactions, volume)
- Pending Topup (approve/reject dengan 1 klik)
- Pending Withdraw (approve/reject dengan 1 klik)
- Coin Settings (enable/disable network per coin)
- Payment Methods (enable/disable)
- Users list

### Legacy Commands
- `/pending_topup` - View pending top ups
- `/pending_withdraw` - View pending withdrawals
- `/approve_topup [id]` - Approve top up
- `/reject_topup [id]` - Reject top up
- `/approve_withdraw [id]` - Approve withdrawal
- `/reject_withdraw [id]` - Reject withdrawal

## Recent Changes
- **2026-01-02**: Fixed ALL 128 pyright type errors properly (no suppressions) - 100% type-safe code
- **2026-01-02**: Replaced all string literals with Prisma enums (TransactionStatus, OrderStatus, UserStatus, TransactionType, OrderType)
- **2026-01-02**: Added proper null checks and isinstance guards for InaccessibleMessage issues
- **2026-01-02**: pyrightconfig.json set to "standard" mode for strict type checking
- **2026-01-02**: Cleaned up all hardcoded values to config.py (bot username, USD_TO_IDR rate)
- **2026-01-02**: Improved admin panel layout - cleaner, more informative with pending counts
- **2026-01-02**: Admin button only appears for users with matching admin IDs
- Admin panel moved to Telegram (no separate web panel needed)
- Interactive inline keyboard for admin actions
- Fixed network names to match OxaPay API exactly (Ethereum, BSC, Tron, etc. instead of ERC20, BEP20, TRC20)
- Network filtering: database controls which networks are active, OxaPay provides fees

## Network Names (OxaPay Standard)
- BTC: Bitcoin
- ETH: Ethereum, BSC, Base
- BNB: BSC
- SOL: Solana
- USDT: Tron, Ethereum, BSC, Polygon, Solana, The Open Network
- USDC: Ethereum, BSC, Solana, Base
