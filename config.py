"""
Конфигурация проекта
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс конфигурации приложения"""
    
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
    
    # TonAPI Key
    TON_API_KEY = os.getenv('TON_API_KEY', 'your_tonapi_key_here')
    
    # Database URL (SQLite по умолчанию)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    
    # Настройки приложения
    APP_NAME = "TON Token Marketplace v3"
    VERSION = "3.0.0"
    DEVELOPER = "Дмитрий Крылосов"
    
    # Адрес мета-токена DKIP
    DKIP_TOKEN_ADDRESS = "EQAp_Ypj8Dz3__S-MMOQf1W0hOVZ63qfCWOvLgnJy15K6rCt"
    
    # Лимиты и настройки
    MAX_TOKENS_PER_USER = 100
    REQUEST_TIMEOUT = 30  # секунд
    CACHE_EXPIRATION = 300  # секунд (5 минут)
