import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Trading Platform Configuration
    TRADING_PLATFORM = os.getenv('TRADING_PLATFORM', 'binance')  # 'binance' ou 'mt5'
    ACCOUNT_TYPE = os.getenv('ACCOUNT_TYPE', 'demo')  # 'demo' ou 'real'
    
    # Binance API Configuration (pour compte réel)
    EXCHANGE = os.getenv('EXCHANGE', 'binance')  # binance, mt5, etc.
    API_KEY = os.getenv('API_KEY', '')
    API_SECRET = os.getenv('API_SECRET', '')
    SANDBOX_MODE = os.getenv('SANDBOX_MODE', 'True').lower() == 'true'
    SUBACCOUNT_NAME = os.getenv('SUBACCOUNT_NAME', '')
    
    # MT5 Configuration (pour compte démo ou réel)
    MT5_LOGIN = os.getenv('MT5_LOGIN', '')  # Optionnel pour démo
    MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')  # Optionnel pour démo
    MT5_SERVER = os.getenv('MT5_SERVER', '')  # Optionnel pour démo
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Trading Configuration
    # Symbole par défaut selon la plateforme
    def get_default_symbol():
        platform = os.getenv('TRADING_PLATFORM', 'binance')
        if platform == 'mt5':
            # Symboles populaires MT5 : Forex et métaux précieux
            return 'XAUUSD'  # Or/USD - très volatil, excellent pour patterns harmoniques
        else:
            return 'BTCUSDT'  # Bitcoin pour Binance
    
    SYMBOL = os.getenv('SYMBOL', get_default_symbol())
    TIMEFRAME_MAIN = '1h'  # Timeframe principal pour détecter les patterns
    TIMEFRAME_ENTRY = '5m'  # Timeframe pour les confirmations d'entrée
    
    # Risk Management
    RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '1.0'))  # 1% du capital par trade
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '3'))
    USE_LEVERAGE = False
    
    # Pattern Detection Settings
    MIN_PATTERN_BARS = 20  # Minimum de barres pour former un pattern
    FIBONACCI_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 0.886]
    TRENDLINE_MIN_TOUCHES = 3
    
    # Zone Settings
    ZONE_BUFFER_PIPS = 5  # Buffer pour les zones en pips
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'harmonic_bot.log'
