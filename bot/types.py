"""
Type definitions for the bot.
Uses Prisma's generated models for proper typing.
"""
from typing import Optional, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from prisma.models import User, Balance, CryptoOrder, Deposit, Withdrawal
    from prisma.enums import UserStatus, OrderStatus, TransactionStatus

# Re-export Prisma models for convenience
try:
    from prisma.models import User, Balance, CryptoOrder, Deposit, Withdrawal
    from prisma.enums import UserStatus, OrderStatus, TransactionStatus
except ImportError:
    pass


class UserWithBalance:
    """Type hint for User with optional balance relation"""
    id: str
    telegramId: int
    username: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    email: Optional[str]
    whatsapp: Optional[str]
    referralCode: str
    status: str
    balance: Optional["Balance"]
