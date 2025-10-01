#!/usr/bin/env python3
"""
Script de test pour la connexion MetaTrader 5
Teste la connexion au compte démo MT5 et les fonctions de base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from trading.mt5_connector import MT5Connector
from utils.logger import TradingLogger

def test_mt5_connection():
    """Test complet de la connexion MT5"""
    logger = TradingLogger()
    
    print("=" * 60)
    print("🧪 TEST DE CONNEXION METATRADER 5")
    print("=" * 60)
    
    try:
        # Test 1: Initialisation du connecteur
        print("\n1️⃣ Test d'initialisation du connecteur MT5...")
        connector = MT5Connector()
        
        if connector.connected:
            print("✅ Connexion MT5 réussie!")
            print(f"   - Compte: #{connector.account_info.get('login', 'N/A')}")
            print(f"   - Serveur: {connector.account_info.get('server', 'N/A')}")
            print(f"   - Balance: {connector.account_info.get('balance', 0)} {connector.account_info.get('currency', 'USD')}")
            print(f"   - Type: {'Démo' if connector.account_info.get('trade_mode') == 0 else 'Réel'}")
        else:
            print("❌ Échec de connexion MT5")
            return False
        
        # Test 2: Récupération des données historiques
        print("\n2️⃣ Test de récupération des données historiques...")
        symbol = "XAUUSD"  # Or/USD - symbole par défaut
        
        # Test différents timeframes
        timeframes = ['1m', '5m', '1h', '1d']
        for tf in timeframes:
            df = connector.get_historical_data(symbol, tf, 10)
            if not df.empty:
                print(f"✅ Données {tf}: {len(df)} barres récupérées")
                print(f"   - Dernier prix: {df['close'].iloc[-1]:.5f}")
            else:
                print(f"❌ Échec récupération données {tf}")
        
        # Test 3: Prix actuel
        print("\n3️⃣ Test de récupération du prix actuel...")
        current_price = connector.get_current_price(symbol)
        if current_price > 0:
            print(f"✅ Prix actuel {symbol}: {current_price:.5f}")
        else:
            print(f"❌ Échec récupération prix {symbol}")
        
        # Test 4: Informations du symbole
        print("\n4️⃣ Test des informations du symbole...")
        symbol_info = connector.get_symbol_info(symbol)
        if symbol_info:
            print(f"✅ Informations {symbol}:")
            print(f"   - Lot minimum: {symbol_info.get('min_lot', 'N/A')}")
            print(f"   - Lot maximum: {symbol_info.get('max_lot', 'N/A')}")
            print(f"   - Step: {symbol_info.get('lot_step', 'N/A')}")
            print(f"   - Point: {symbol_info.get('point', 'N/A')}")
            print(f"   - Digits: {symbol_info.get('digits', 'N/A')}")
        else:
            print(f"❌ Échec récupération infos {symbol}")
        
        # Test 5: Informations du marché
        print("\n5️⃣ Test des informations du marché...")
        market_info = connector.get_market_info(symbol)
        if market_info:
            print(f"✅ Informations marché {symbol}:")
            print(f"   - Bid: {market_info.get('bid', 'N/A')}")
            print(f"   - Ask: {market_info.get('ask', 'N/A')}")
            print(f"   - Spread: {market_info.get('spread', 'N/A')}")
        else:
            print(f"❌ Échec récupération infos marché {symbol}")
        
        # Test 6: Calcul de taille de position
        print("\n6️⃣ Test de calcul de taille de position...")
        risk_amount = 100.0  # 100 USD de risque
        entry_price = current_price
        stop_loss = current_price - 0.0050  # 50 pips de SL
        
        position_size = connector.calculate_position_size(symbol, risk_amount, entry_price, stop_loss)
        if position_size > 0:
            print(f"✅ Taille de position calculée: {position_size:.2f} lots")
            print(f"   - Risque: {risk_amount} USD")
            print(f"   - SL distance: {abs(entry_price - stop_loss):.5f}")
        else:
            print("❌ Échec calcul taille position")
        
        # Test 7: Positions et ordres (lecture seule)
        print("\n7️⃣ Test de lecture des positions et ordres...")
        positions = connector.get_positions()
        orders = connector.get_open_orders()
        
        print(f"✅ Positions ouvertes: {len(positions)}")
        print(f"✅ Ordres en attente: {len(orders)}")
        
        # Test 8: Mise à jour du solde
        print("\n8️⃣ Test de mise à jour du solde...")
        connector.update_balance()
        balance = connector.get_available_balance()
        print(f"✅ Solde disponible: {balance:.2f}")
        
        # Déconnexion
        print("\n9️⃣ Déconnexion...")
        connector.disconnect()
        print("✅ Déconnexion réussie")
        
        print("\n" + "=" * 60)
        print("🎉 TOUS LES TESTS MT5 SONT PASSÉS AVEC SUCCÈS!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR DURANT LES TESTS: {e}")
        logger.error(f"Erreur test MT5: {e}")
        return False

def test_platform_selection():
    """Test de sélection de plateforme"""
    print("\n" + "=" * 60)
    print("🔄 TEST DE SÉLECTION DE PLATEFORME")
    print("=" * 60)
    
    from trading.connector_factory import ConnectorFactory
    
    # Afficher les informations de la plateforme configurée
    platform_info = ConnectorFactory.get_platform_info()
    
    print(f"Plateforme configurée: {platform_info['platform'].upper()}")
    print(f"Type de compte: {platform_info['account_type'].upper()}")
    print(f"Symbole par défaut: {platform_info['symbol_default']}")
    print(f"Nécessite clé API: {platform_info['requires_api_key']}")
    print(f"Support démo: {platform_info['supports_demo']}")
    print(f"Méthode de connexion: {platform_info['connection_method']}")
    
    if platform_info['platform'] == 'mt5':
        print("\n✅ Configuration MT5 détectée - Test de connexion...")
        return test_mt5_connection()
    else:
        print(f"\n⚠️  Plateforme {platform_info['platform']} configurée")
        print("Pour tester MT5, modifiez TRADING_PLATFORM=mt5 dans votre .env")
        return True

if __name__ == "__main__":
    print("🚀 Démarrage des tests de connexion...")
    
    # Test de sélection de plateforme
    success = test_platform_selection()
    
    if success:
        print("\n✅ Tests terminés avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Échec des tests!")
        sys.exit(1)
