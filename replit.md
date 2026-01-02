# Crypto Trading Telegram Bot

## Overview

This is a Telegram bot for cryptocurrency trading, built with Python using the aiogram framework. The bot enables users to buy and sell cryptocurrencies (BTC, ETH, BNB, SOL, USDT, USDC) with Indonesian Rupiah (IDR), manage their balance through top-ups and withdrawals, and participate in a referral program.

The bot integrates with OxaPay for cryptocurrency payment processing and CryptoBot for stablecoin deposits. It features user authentication, PIN security, transaction history, and an admin panel for managing pending transactions and coin settings.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **aiogram 3.13** - Modern async Telegram bot framework
- Uses webhook mode for production deployment (Railway) with fallback support for polling
- FSM (Finite State Machine) storage uses in-memory storage for conversation state management

### Database Layer
- **Prisma ORM** with PostgreSQL database
- Schema defined externally (referenced via `BOT_DATABASE` environment variable)
- Models include: User, Balance, Transaction, Deposit, Withdrawal, CryptoOrder, CoinSetting, PaymentMethod, ReferralSetting
- Enums: UserStatus, OrderStatus, TransactionStatus, TransactionType, OrderType

### Middleware Stack
1. **LoggingMiddleware** - Request/response logging
2. **ThrottlingMiddleware** - Rate limiting (0.1s between requests per user)
3. **DatabaseMiddleware** - Injects Prisma client and OxaPay service
4. **UserStatusMiddleware** - User authentication and activity tracking with 30s cache

### Caching Strategy
- **TTLCache** from cachetools library for in-memory caching
- Balance cache: 5s TTL, 5000 entries
- Coin settings cache: 10s TTL
- User cache: 30s TTL for real-time data
- API response caching for OxaPay prices and currencies

### Background Task Processing
- Heavy operations (payouts, cache warming) processed asynchronously
- Target response time: 100-200ms per handler
- Uses asyncio for concurrent API calls via `ParallelAPIService`

### Handler Organization
Modular router structure with dedicated handlers for:
- User onboarding (start, signup)
- Core features (balance, buy, sell, topup, withdraw)
- Supporting features (history, settings, referral, stock)
- Admin operations (pending transactions, coin management, user management)

### Configuration
- Environment-based configuration via python-dotenv
- Supports multiple deployment environments (Replit, Railway)
- Config dataclasses for type safety: BotConfig, DatabaseConfig, OxaPayConfig, CryptoBotConfig

## External Dependencies

### Payment Processors
- **OxaPay API** - Primary cryptocurrency payment gateway
  - Merchant API for receiving payments
  - Payout API for sending crypto
  - Webhook integration for payment status updates
  - Exchange rate fetching

- **CryptoBot (Telegram)** - Stablecoin deposits (USDT/USDC)
  - Invoice creation for deposits
  - Exchange rate management with configurable margin

### Database
- **PostgreSQL** via Prisma ORM
- Connection managed through `DATABASE_URL` or `BOT_DATABASE` environment variable
- Auto-reconnection handling in DatabaseMiddleware

### Infrastructure
- **Railway** - Production deployment platform
- Dockerfile-based builds
- Webhook endpoint at `/telegram/webhook`
- OxaPay webhook at `/webhook/oxapay`
- Health check endpoint available

### Key Environment Variables
- `TELEGRAM_BOT_TOKEN` - Bot authentication
- `BOT_DATABASE` / `DATABASE_URL` - PostgreSQL connection
- `ADMIN_TELEGRAM_IDS` - Comma-separated admin user IDs
- `OXAPAY_MERCHANT_API_KEY`, `OXAPAY_PAYOUT_API_KEY`, `OXAPAY_WEBHOOK_SECRET`
- `CRYPTOBOT_API_TOKEN`
- `WEBHOOK_HOST` / `RAILWAY_PUBLIC_DOMAIN` - Webhook URL configuration
- `USD_TO_IDR` - Exchange rate for currency conversion