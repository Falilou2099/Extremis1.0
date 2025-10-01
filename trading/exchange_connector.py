import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from config import Config
from utils.logger import TradingLogger
import asyncio

class ExchangeConnector:
    def __init__(self):
        self.logger = TradingLogger()
        self.exchange = None
        self.positions = {}
        self.balance = {}
        self.connect_to_exchange()
    
    def connect_to_exchange(self):
        """Connexion à l'exchange"""
        try:
            if Config.EXCHANGE.lower() == 'binance':
                self.exchange = ccxt.binance({
                    'apiKey': Config.API_KEY,
                    'secret': Config.API_SECRET,
                    'sandbox': Config.SANDBOX_MODE,
                    'enableRateLimit': True,
                })
            else:
                raise ValueError(f"Exchange {Config.EXCHANGE} non supporté")
            
            # Test de connexion
            self.exchange.load_markets()
            
            # Log avec info du sous-compte si configuré
            account_info = f"{Config.EXCHANGE}"
            if Config.SUBACCOUNT_NAME:
                account_info += f" (Sous-compte: {Config.SUBACCOUNT_NAME})"
            
            self.logger.info(f"Connexion réussie à {account_info}")
            
            # Charger le solde initial
            self.update_balance()
            
        except Exception as e:
            self.logger.error(f"Erreur connexion exchange: {e}")
            raise
    
    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Récupère les données historiques OHLCV"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erreur récupération données {symbol} {timeframe}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            self.logger.error(f"Erreur récupération prix {symbol}: {e}")
            return 0.0
    
    def calculate_position_size(self, symbol: str, risk_amount: float, entry_price: float, stop_loss: float) -> float:
        """Calcule la taille de position basée sur le risque"""
        try:
            # Récupérer les infos du marché
            market = self.exchange.market(symbol)
            
            # Calculer le risque par unité
            risk_per_unit = abs(entry_price - stop_loss)
            
            if risk_per_unit == 0:
                return 0
            
            # Calculer la quantité
            quantity = risk_amount / risk_per_unit
            
            # Appliquer les contraintes du marché
            min_amount = market['limits']['amount']['min']
            max_amount = market['limits']['amount']['max']
            
            if min_amount:
                quantity = max(quantity, min_amount)
            if max_amount:
                quantity = min(quantity, max_amount)
            
            # Arrondir selon la précision du marché
            precision = market['precision']['amount']
            quantity = round(quantity, precision)
            
            return quantity
            
        except Exception as e:
            self.logger.error(f"Erreur calcul taille position: {e}")
            return 0
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """Place un ordre au marché"""
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            
            self.logger.trade_log(
                f"ORDRE_{side.upper()}", 
                symbol, 
                order.get('price', 0), 
                amount,
                "Ordre au marché"
            )
            
            return order
            
        except Exception as e:
            self.logger.error(f"Erreur ordre marché {side} {symbol}: {e}")
            return None
    
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """Place un ordre limite"""
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            
            self.logger.trade_log(
                f"ORDRE_LIMITE_{side.upper()}", 
                symbol, 
                price, 
                amount,
                "Ordre limite"
            )
            
            return order
            
        except Exception as e:
            self.logger.error(f"Erreur ordre limite {side} {symbol}: {e}")
            return None
    
    def place_stop_loss_order(self, symbol: str, side: str, amount: float, stop_price: float) -> Optional[Dict]:
        """Place un ordre stop loss"""
        try:
            # Pour Binance, utiliser un ordre stop market
            order = self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=side,
                amount=amount,
                params={'stopPrice': stop_price}
            )
            
            self.logger.trade_log(
                f"STOP_LOSS_{side.upper()}", 
                symbol, 
                stop_price, 
                amount,
                "Stop loss"
            )
            
            return order
            
        except Exception as e:
            self.logger.error(f"Erreur stop loss {side} {symbol}: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Annule un ordre"""
        try:
            self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Ordre {order_id} annulé pour {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur annulation ordre {order_id}: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Récupère les ordres ouverts"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            self.logger.error(f"Erreur récupération ordres ouverts: {e}")
            return []
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Récupère les positions ouvertes"""
        try:
            if hasattr(self.exchange, 'fetch_positions'):
                positions = self.exchange.fetch_positions([symbol] if symbol else None)
                # Filtrer les positions avec une taille > 0
                return [pos for pos in positions if float(pos['size']) > 0]
            else:
                # Pour les exchanges spot, simuler les positions
                return self._simulate_spot_positions(symbol)
        except Exception as e:
            self.logger.error(f"Erreur récupération positions: {e}")
            return []
    
    def _simulate_spot_positions(self, symbol: str = None) -> List[Dict]:
        """Simule les positions pour le trading spot"""
        positions = []
        
        try:
            balance = self.exchange.fetch_balance()
            
            for currency, amount_info in balance.items():
                if currency == 'info':
                    continue
                
                free = amount_info.get('free', 0)
                used = amount_info.get('used', 0)
                total = amount_info.get('total', 0)
                
                if total > 0 and currency != 'USDT':  # Exclure USDT (devise de base)
                    positions.append({
                        'symbol': f"{currency}/USDT",
                        'size': total,
                        'side': 'long',
                        'unrealizedPnl': 0,  # À calculer si nécessaire
                        'percentage': 0
                    })
        
        except Exception as e:
            self.logger.error(f"Erreur simulation positions spot: {e}")
        
        return positions
    
    def update_balance(self):
        """Met à jour le solde du compte"""
        try:
            self.balance = self.exchange.fetch_balance()
            usdt_balance = self.balance.get('USDT', {}).get('free', 0)
            self.logger.info(f"Solde USDT disponible: {usdt_balance}")
        except Exception as e:
            self.logger.error(f"Erreur mise à jour solde: {e}")
    
    def get_available_balance(self, currency: str = 'USDT') -> float:
        """Retourne le solde disponible pour une devise"""
        try:
            return self.balance.get(currency, {}).get('free', 0)
        except:
            return 0
    
    def calculate_risk_amount(self, total_balance: float, risk_percentage: float = None) -> float:
        """Calcule le montant à risquer par trade"""
        if risk_percentage is None:
            risk_percentage = Config.RISK_PERCENTAGE
        
        return total_balance * (risk_percentage / 100)
    
    def get_market_info(self, symbol: str) -> Dict:
        """Récupère les informations du marché"""
        try:
            market = self.exchange.market(symbol)
            ticker = self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'min_amount': market['limits']['amount']['min'],
                'max_amount': market['limits']['amount']['max'],
                'min_price': market['limits']['price']['min'],
                'max_price': market['limits']['price']['max'],
                'amount_precision': market['precision']['amount'],
                'price_precision': market['precision']['price'],
                'current_price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume']
            }
        except Exception as e:
            self.logger.error(f"Erreur info marché {symbol}: {e}")
            return {}
    
    def close_position(self, symbol: str, amount: float = None) -> Optional[Dict]:
        """Ferme une position (pour le spot, vend tout)"""
        try:
            positions = self.get_positions(symbol)
            
            if not positions:
                self.logger.warning(f"Aucune position à fermer pour {symbol}")
                return None
            
            position = positions[0]
            close_amount = amount if amount else position['size']
            
            # Pour le spot, toujours vendre
            order = self.place_market_order(symbol, 'sell', close_amount)
            
            if order:
                self.logger.trade_log(
                    "FERMETURE_POSITION", 
                    symbol, 
                    order.get('price', 0), 
                    close_amount,
                    "Fermeture automatique"
                )
            
            return order
            
        except Exception as e:
            self.logger.error(f"Erreur fermeture position {symbol}: {e}")
            return None
