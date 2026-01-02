import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BotConfig:
    token: str
    admin_ids: list[int]


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class OxaPayConfig:
    merchant_api_key: str
    payout_api_key: str
    webhook_secret: str
    webhook_url: str
    base_url: str = "https://api.oxapay.com"


@dataclass
class CryptoBotConfig:
    api_token: str
    margin: float = 0.05


@dataclass
class AppConfig:
    bot: BotConfig
    database: DatabaseConfig
    oxapay: OxaPayConfig
    cryptobot: CryptoBotConfig
    webhook_host: str
    debug: bool = False


def load_config() -> AppConfig:
    admin_ids_str = os.getenv("ADMIN_TELEGRAM_IDS", "")
    admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
    
    replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
    webhook_host = os.getenv("WEBHOOK_HOST", replit_domain)
    
    return AppConfig(
        bot=BotConfig(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            admin_ids=admin_ids,
        ),
        database=DatabaseConfig(
            url=os.getenv("BOT_DATABASE", ""),
        ),
        oxapay=OxaPayConfig(
            merchant_api_key=os.getenv("OXAPAY_MERCHANT_API_KEY", ""),
            payout_api_key=os.getenv("OXAPAY_PAYOUT_API_KEY", ""),
            webhook_secret=os.getenv("OXAPAY_WEBHOOK_SECRET", ""),
            webhook_url=os.getenv("OXAPAY_WEBHOOK_URL", f"https://{webhook_host}/webhook/oxapay"),
        ),
        cryptobot=CryptoBotConfig(
            api_token=os.getenv("CRYPTOBOT_API_TOKEN", ""),
            margin=float(os.getenv("CRYPTOBOT_MARGIN", "0.05")),
        ),
        webhook_host=webhook_host,
        debug=os.getenv("DEBUG", "false").lower() == "true",
    )


config = load_config()
