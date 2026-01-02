import random
import string
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


def generate_referral_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r'\D', '', phone)
    
    if cleaned.startswith('62'):
        cleaned = '0' + cleaned[2:]
    
    if cleaned.startswith('0') and len(cleaned) >= 10 and len(cleaned) <= 15:
        return True
    
    return False


def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'\D', '', phone)
    
    if cleaned.startswith('0'):
        cleaned = '62' + cleaned[1:]
    elif not cleaned.startswith('62'):
        cleaned = '62' + cleaned
    
    return cleaned


def parse_amount(text: str) -> Optional[Decimal]:
    try:
        cleaned = text.replace(',', '').replace('.', '').strip()
        cleaned = re.sub(r'[^\d]', '', cleaned)
        
        if cleaned:
            return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        pass
    
    return None


def parse_crypto_amount(text: str) -> Optional[Decimal]:
    try:
        cleaned = text.replace(',', '.').strip()
        cleaned = re.sub(r'[^\d.]', '', cleaned)
        
        if cleaned:
            return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        pass
    
    return None


def format_large_number(num: Decimal) -> str:
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"
    return str(num)


def truncate_address(address: str, start: int = 6, end: int = 4) -> str:
    if len(address) <= start + end:
        return address
    return f"{address[:start]}...{address[-end:]}"


def calculate_buy_price(
    crypto_amount: Decimal,
    rate: Decimal,
    margin_percent: Decimal,
    network_fee: Decimal
) -> dict:
    margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
    rate_with_margin = rate * margin_multiplier
    
    subtotal = crypto_amount * rate_with_margin
    network_fee_idr = network_fee * rate
    total = subtotal + network_fee_idr
    
    return {
        "rate_with_margin": rate_with_margin,
        "subtotal": subtotal,
        "network_fee_idr": network_fee_idr,
        "total": total,
    }


def calculate_sell_price(
    crypto_amount: Decimal,
    rate: Decimal,
    margin_percent: Decimal
) -> dict:
    margin_multiplier = Decimal('1') - (margin_percent / Decimal('100'))
    rate_with_margin = rate * margin_multiplier
    
    total = crypto_amount * rate_with_margin
    
    return {
        "rate_with_margin": rate_with_margin,
        "total": total,
    }


def idr_to_crypto(
    idr_amount: Decimal,
    rate: Decimal,
    margin_percent: Decimal,
    network_fee: Decimal
) -> dict:
    margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
    rate_with_margin = rate * margin_multiplier
    
    network_fee_idr = network_fee * rate
    available_for_crypto = idr_amount - network_fee_idr
    
    if available_for_crypto <= 0:
        return {
            "crypto_amount": Decimal('0'),
            "rate_with_margin": rate_with_margin,
            "network_fee_idr": network_fee_idr,
            "total_idr": idr_amount,
            "error": "Amount too low to cover network fee",
        }
    
    crypto_amount = available_for_crypto / rate_with_margin
    
    return {
        "crypto_amount": crypto_amount,
        "rate_with_margin": rate_with_margin,
        "network_fee_idr": network_fee_idr,
        "total_idr": idr_amount,
    }
