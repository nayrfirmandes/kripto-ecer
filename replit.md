# Crypto Trading Telegram Bot

## Overview
Telegram bot untuk jual beli cryptocurrency dengan sistem saldo internal. Bot ini terintegrasi dengan OxaPay untuk transaksi crypto.

## Tech Stack
- **Bot**: Python 3.11 + Aiogram 3.x
- **Database**: PostgreSQL (NeonSQL)
- **ORM**: Prisma
- **Admin Panel**: Next.js (planned)

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

admin-panel/             # Next.js admin (planned)
```

## Environment Variables
Required secrets:
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `DATABASE_URL` - NeonSQL connection string
- `OXAPAY_API_KEY` - OxaPay API key
- `OXAPAY_MERCHANT_ID` - OxaPay merchant ID
- `OXAPAY_WEBHOOK_SECRET` - Webhook verification secret
- `ADMIN_TELEGRAM_IDS` - Comma-separated admin Telegram IDs

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

## Admin Commands (Telegram)
- `/admin` - Admin dashboard
- `/pending_topup` - View pending top ups
- `/pending_withdraw` - View pending withdrawals
- `/approve_topup [id]` - Approve top up
- `/reject_topup [id]` - Reject top up
- `/approve_withdraw [id]` - Approve withdrawal
- `/reject_withdraw [id]` - Reject withdrawal

## Recent Changes
- Fixed admin panel and bot database sync - both now use BOT_DATABASE (NeonSQL external)
- Fixed network names to match OxaPay API exactly (Ethereum, BSC, Tron, etc. instead of ERC20, BEP20, TRC20)
- Admin panel prisma client now uses datasourceUrl: process.env.BOT_DATABASE
- Coin settings cache TTL reduced to 10 seconds for faster sync
- Network filtering: database controls which networks are active, OxaPay provides fees
- Initial setup with all handlers
- Prisma schema with all models
- OxaPay integration for payments
- Webhook endpoint for crypto confirmations

## Network Names (OxaPay Standard)
- BTC: Bitcoin
- ETH: Ethereum, BSC, Base
- BNB: BSC
- SOL: Solana
- USDT: Tron, Ethereum, BSC, Polygon, Solana, The Open Network
- USDC: Ethereum, BSC, Solana, Base
