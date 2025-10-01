#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion au sous-compte Binance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from trading.exchange_connector import ExchangeConnector
from utils.logger import TradingLogger

def test_subaccount_connection():
    """Test de connexion au sous-compte"""
    logger = TradingLogger()
    
    try:
        logger.info("🧪 Test de connexion au sous-compte Binance")
        logger.info(f"Exchange: {Config.EXCHANGE}")
        logger.info(f"Mode Sandbox: {Config.SANDBOX_MODE}")
        
        if Config.SUBACCOUNT_NAME:
            logger.info(f"Sous-compte: {Config.SUBACCOUNT_NAME}")
        else:
            logger.warning("Aucun nom de sous-compte configuré")
        
        # Test de connexion
        exchange = ExchangeConnector()
        
        # Vérifier le solde
        balance = exchange.get_available_balance('USDT')
        logger.info(f"💰 Solde USDT disponible: {balance}")
        
        # Vérifier les informations du compte
        account_info = exchange.exchange.fetch_balance()
        logger.info(f"📊 Informations du compte récupérées avec succès")
        
        # Afficher quelques devises avec solde > 0
        currencies_with_balance = []
        for currency, info in account_info.items():
            if currency != 'info' and isinstance(info, dict):
                total = info.get('total', 0)
                if total > 0:
                    currencies_with_balance.append(f"{currency}: {total}")
        
        if currencies_with_balance:
            logger.info(f"💼 Devises avec solde: {', '.join(currencies_with_balance[:5])}")
        else:
            logger.info("💼 Aucune devise avec solde détectée")
        
        # Test de récupération des données de marché
        symbol = Config.SYMBOL
        current_price = exchange.get_current_price(symbol)
        logger.info(f"📈 Prix actuel {symbol}: {current_price}")
        
        logger.info("✅ Test de connexion au sous-compte réussi!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de connexion: {e}")
        return False

if __name__ == "__main__":
    success = test_subaccount_connection()
    sys.exit(0 if success else 1)
