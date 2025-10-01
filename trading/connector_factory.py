from config import Config
from trading.exchange_connector import ExchangeConnector
from trading.mt5_connector import MT5Connector
from utils.logger import TradingLogger

class ConnectorFactory:
    """Factory pour créer le bon connecteur selon la configuration"""
    
    @staticmethod
    def create_connector():
        """Crée et retourne le connecteur approprié selon la configuration"""
        logger = TradingLogger()
        
        # Déterminer le type de plateforme et de compte
        platform = Config.TRADING_PLATFORM.lower()
        account_type = Config.ACCOUNT_TYPE.lower()
        
        logger.info(f"Initialisation du connecteur - Plateforme: {platform}, Type: {account_type}")
        
        if platform == 'mt5':
            # Utiliser MT5 pour les comptes démo ou réels MT5
            logger.info("Connexion à MetaTrader 5...")
            return MT5Connector()
            
        elif platform == 'binance':
            # Utiliser Binance pour les comptes réels ou sandbox
            if account_type == 'demo':
                logger.info("Connexion à Binance en mode sandbox (démo)...")
                # Forcer le mode sandbox pour les comptes démo Binance
                Config.SANDBOX_MODE = True
            else:
                logger.info("Connexion à Binance en mode réel...")
                Config.SANDBOX_MODE = False
            
            return ExchangeConnector()
            
        else:
            raise ValueError(f"Plateforme non supportée: {platform}")
    
    @staticmethod
    def get_platform_info():
        """Retourne les informations sur la plateforme configurée"""
        platform = Config.TRADING_PLATFORM.lower()
        account_type = Config.ACCOUNT_TYPE.lower()
        
        info = {
            'platform': platform,
            'account_type': account_type,
            'symbol_default': Config.SYMBOL
        }
        
        if platform == 'mt5':
            info.update({
                'requires_api_key': False,
                'supports_demo': True,
                'default_symbols': ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD'],
                'connection_method': 'MT5 Terminal'
            })
        elif platform == 'binance':
            info.update({
                'requires_api_key': True,
                'supports_demo': True,  # Via sandbox
                'default_symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT'],
                'connection_method': 'REST API'
            })
        
        return info
