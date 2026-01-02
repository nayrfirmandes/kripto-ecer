from decimal import Decimal
from typing import Optional
from datetime import datetime
from prisma import Prisma, Json
from prisma.models import User, Balance, Transaction, Deposit, Withdrawal, CryptoOrder, CoinSetting, PaymentMethod, ReferralSetting


async def get_user_by_telegram_id(db: Prisma, telegram_id: int) -> Optional[User]:
    return await db.user.find_unique(
        where={"telegramId": telegram_id},
        include={"balance": True}
    )


async def create_user(
    db: Prisma,
    telegram_id: int,
    referral_code: str,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    whatsapp: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    referred_by_id: Optional[str] = None,
) -> User:
    user = await db.user.create(
        data={
            "telegramId": telegram_id,
            "username": username,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "whatsapp": whatsapp,
            "latitude": latitude,
            "longitude": longitude,
            "referralCode": referral_code,
            "referredById": referred_by_id,
            "status": "ACTIVE",
        }
    )
    
    await db.balance.create(
        data={
            "userId": user.id,
            "amount": Decimal("0"),
        }
    )
    
    return await db.user.find_unique(
        where={"id": user.id},
        include={"balance": True}
    )


async def get_user_balance(db: Prisma, user_id: str) -> Decimal:
    balance = await db.balance.find_unique(where={"userId": user_id})
    return balance.amount if balance else Decimal("0")


async def update_balance(db: Prisma, user_id: str, amount: Decimal) -> Balance:
    result = await db.balance.update(
        where={"userId": user_id},
        data={"amount": {"increment": amount}}
    )
    
    # Invalidate balance cache after update for real-time consistency
    try:
        from bot.services.cache import cache_service
        cache_service.invalidate_balance(user_id)
    except ImportError:
        pass
    
    return result


async def get_user_by_referral_code(db: Prisma, code: str) -> Optional[User]:
    return await db.user.find_unique(where={"referralCode": code})


async def get_user_by_email(db: Prisma, email: str) -> Optional[User]:
    return await db.user.find_first(where={"email": email})


async def get_user_by_whatsapp(db: Prisma, whatsapp: str) -> Optional[User]:
    return await db.user.find_first(where={"whatsapp": whatsapp})


async def create_deposit(
    db: Prisma,
    user_id: str,
    amount: Decimal,
    payment_method: str,
) -> Deposit:
    deposit = await db.deposit.create(
        data={
            "userId": user_id,
            "amount": amount,
            "paymentMethod": payment_method,
            "status": "PENDING",
        }
    )
    
    await db.transaction.create(
        data={
            "user": {"connect": {"id": user_id}},
            "type": "TOPUP",
            "amount": amount,
            "status": "PENDING",
            "description": f"Deposit via {payment_method}",
            "metadata": Json({"depositId": deposit.id}),
        }
    )
    
    return deposit


async def create_withdrawal(
    db: Prisma,
    user_id: str,
    amount: Decimal,
    bank_name: Optional[str] = None,
    account_number: Optional[str] = None,
    account_name: Optional[str] = None,
    ewallet_type: Optional[str] = None,
    ewallet_number: Optional[str] = None,
) -> Withdrawal:
    withdrawal = await db.withdrawal.create(
        data={
            "userId": user_id,
            "amount": amount,
            "bankName": bank_name,
            "accountNumber": account_number,
            "accountName": account_name,
            "ewalletType": ewallet_type,
            "ewalletNumber": ewallet_number,
            "status": "PENDING",
        }
    )
    
    await db.transaction.create(
        data={
            "user": {"connect": {"id": user_id}},
            "type": "WITHDRAW",
            "amount": amount,
            "status": "PENDING",
            "description": f"Withdraw to {bank_name or ewallet_type}",
            "metadata": Json({"withdrawalId": withdrawal.id}),
        }
    )
    
    return withdrawal


async def create_crypto_order(
    db: Prisma,
    user_id: str,
    order_type: str,
    coin_symbol: str,
    network: str,
    crypto_amount: Decimal,
    fiat_amount: Decimal,
    rate: Decimal,
    margin: Decimal,
    network_fee: Decimal,
    wallet_address: Optional[str] = None,
    deposit_address: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    oxapay_payment_id: Optional[str] = None,
    oxapay_payout_id: Optional[str] = None,
) -> CryptoOrder:
    return await db.cryptoorder.create(
        data={
            "userId": user_id,
            "orderType": order_type,
            "coinSymbol": coin_symbol,
            "network": network,
            "cryptoAmount": crypto_amount,
            "fiatAmount": fiat_amount,
            "rate": rate,
            "margin": margin,
            "networkFee": network_fee,
            "walletAddress": wallet_address,
            "depositAddress": deposit_address,
            "status": "PENDING",
            "expiresAt": expires_at,
            "oxapayPaymentId": oxapay_payment_id,
            "oxapayPayoutId": oxapay_payout_id,
        }
    )


async def get_coin_settings(db: Prisma, coin_symbol: str, network: str) -> Optional[CoinSetting]:
    return await db.coinsetting.find_unique(
        where={"coinSymbol_network": {"coinSymbol": coin_symbol, "network": network}}
    )


async def get_active_coin_settings(db: Prisma) -> list[CoinSetting]:
    return await db.coinsetting.find_many(where={"isActive": True})


async def get_payment_methods(db: Prisma, is_active: bool = True) -> list[PaymentMethod]:
    return await db.paymentmethod.find_many(where={"isActive": is_active})


async def get_referral_setting(db: Prisma) -> Optional[ReferralSetting]:
    return await db.referralsetting.find_first(where={"isActive": True})


async def get_user_transactions(
    db: Prisma,
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    tx_type: Optional[str] = None,
) -> list[Transaction]:
    where = {"userId": user_id}
    if tx_type:
        where["type"] = tx_type
    
    return await db.transaction.find_many(
        where=where,
        order={"createdAt": "desc"},
        take=limit,
        skip=offset,
    )


async def count_user_transactions(
    db: Prisma,
    user_id: str,
    tx_type: Optional[str] = None,
) -> int:
    where = {"userId": user_id}
    if tx_type:
        where["type"] = tx_type
    
    return await db.transaction.count(where=where)


async def get_referral_count(db: Prisma, user_id: str) -> int:
    return await db.user.count(where={"referredById": user_id})


async def get_referral_bonus_earned(db: Prisma, user_id: str) -> Decimal:
    transactions = await db.transaction.find_many(
        where={
            "userId": user_id,
            "type": "REFERRAL_BONUS",
            "status": "COMPLETED",
        }
    )
    
    return sum(tx.amount for tx in transactions)


async def process_referral_bonus(
    db: Prisma,
    referrer_id: str,
    referee_id: str,
    referrer_bonus: Decimal,
    referee_bonus: Decimal,
):
    if referrer_bonus > 0:
        await update_balance(db, referrer_id, referrer_bonus)
        await db.transaction.create(
            data={
                "userId": referrer_id,
                "type": "REFERRAL_BONUS",
                "amount": referrer_bonus,
                "status": "COMPLETED",
                "description": "Bonus referral",
            }
        )
    
    if referee_bonus > 0:
        await update_balance(db, referee_id, referee_bonus)
        await db.transaction.create(
            data={
                "userId": referee_id,
                "type": "REFERRAL_BONUS",
                "amount": referee_bonus,
                "status": "COMPLETED",
                "description": "Bonus pendaftaran",
            }
        )
