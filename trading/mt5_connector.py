import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from config import Config
from utils.logger import TradingLogger

class MT5Connector:
    def __init__(self):
        self.logger = TradingLogger()
        self.connected = False
        self.account_info = {}
        self.positions = {}
        self.balance = {}
        self.connect_to_mt5()
    
    def connect_to_mt5(self):
        """Connexion à MetaTrader 5"""
        try:
            # Initialiser MT5
            if not mt5.initialize():
                error = mt5.last_error()
                raise Exception(f"Échec initialisation MT5: {error}")
            
            # Connexion au compte démo (pas besoin de login/password pour démo par défaut)
            if hasattr(Config, 'MT5_LOGIN') and Config.MT5_LOGIN:
                # Connexion avec login/password/serveur spécifiques
                authorized = mt5.login(
                    login=int(Config.MT5_LOGIN),
                    password=Config.MT5_PASSWORD,
                    server=Config.MT5_SERVER
                )
                if not authorized:
                    error = mt5.last_error()
                    raise Exception(f"Échec connexion MT5: {error}")
            
            # Récupérer les infos du compte
            self.account_info = mt5.account_info()._asdict() if mt5.account_info() else {}
            
            self.connected = True
            
            account_type = "Démo" if self.account_info.get('trade_mode') == 0 else "Réel"
            self.logger.info(f"Connexion MT5 réussie - Compte {account_type} #{self.account_info.get('login', 'N/A')}")
            self.logger.info(f"Serveur: {self.account_info.get('server', 'N/A')}")
            self.logger.info(f"Balance: {self.account_info.get('balance', 0)} {self.account_info.get('currency', 'USD')}")
            
            # Charger le solde initial
            self.update_balance()
            
        except Exception as e:
            self.logger.error(f"Erreur connexion MT5: {e}")
            self.connected = False
            raise
    
    def disconnect(self):
        """Déconnexion de MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("Déconnexion MT5 réussie")
    
    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Récupère les données historiques OHLCV"""
        try:
            if not self.connected:
                raise Exception("MT5 non connecté")
            
            # Conversion des timeframes
            mt5_timeframe = self._convert_timeframe(timeframe)
            
            # Récupérer les données
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, limit)
            
            if rates is None or len(rates) == 0:
                self.logger.warning(f"Aucune donnée pour {symbol} {timeframe}")
                return pd.DataFrame()
            
            # Convertir en DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Renommer les colonnes pour correspondre à l'interface standard
            df.rename(columns={
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            }, inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            self.logger.error(f"Erreur récupération données MT5 {symbol} {timeframe}: {e}")
            return pd.DataFrame()
    
    def _convert_timeframe(self, timeframe: str) -> int:
        """Convertit le timeframe string en constante MT5"""
        timeframe_map = {
            '1m': mt5.TIMEFRAME_M1,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1M': mt5.TIMEFRAME_MN1
        }
        return timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
    
    def get_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel"""
        try:
            if not self.connected:
                return 0.0
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return 0.0
            
            return tick.bid  # Ou tick.ask selon le besoin
            
        except Exception as e:
            self.logger.error(f"Erreur récupération prix MT5 {symbol}: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Récupère les informations du symbole"""
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return {}
            
            return {
                'symbol': symbol,
                'min_lot': info.volume_min,
                'max_lot': info.volume_max,
                'lot_step': info.volume_step,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'trade_mode': info.trade_mode
            }
        except Exception as e:
            self.logger.error(f"Erreur info symbole MT5 {symbol}: {e}")
            return {}
    
    def calculate_position_size(self, symbol: str, risk_amount: float, entry_price: float, stop_loss: float) -> float:
        """Calcule la taille de position basée sur le risque"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return 0
            
            # Calculer le risque par lot
            point_value = symbol_info.get('point', 0.0001)
            risk_points = abs(entry_price - stop_loss) / point_value
            
            if risk_points == 0:
                return 0
            
            # Calculer la valeur d'un point (approximation pour les paires majeures)
            # Pour une estimation plus précise, il faudrait utiliser les spécifications du contrat
            point_value_money = 1.0  # À ajuster selon le symbole
            
            # Calculer la taille de position
            lot_size = risk_amount / (risk_points * point_value_money)
            
            # Appliquer les contraintes du symbole
            min_lot = symbol_info.get('min_lot', 0.01)
            max_lot = symbol_info.get('max_lot', 100.0)
            lot_step = symbol_info.get('lot_step', 0.01)
            
            lot_size = max(lot_size, min_lot)
            lot_size = min(lot_size, max_lot)
            
            # Arrondir selon le step
            lot_size = round(lot_size / lot_step) * lot_step
            
            return lot_size
            
        except Exception as e:
            self.logger.error(f"Erreur calcul taille position MT5: {e}")
            return 0
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """Place un ordre au marché"""
        try:
            if not self.connected:
                return None
            
            # Préparer la requête
            order_type = mt5.ORDER_TYPE_BUY if side.lower() == 'buy' else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": amount,
                "type": order_type,
                "deviation": 20,
                "magic": 234000,
                "comment": "Harmonic Bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Envoyer l'ordre
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erreur ordre MT5: {result.comment}")
                return None
            
            self.logger.trade_log(
                f"ORDRE_{side.upper()}", 
                symbol, 
                result.price, 
                amount,
                "Ordre au marché MT5"
            )
            
            return {
                'id': result.order,
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': result.price,
                'status': 'filled'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur ordre marché MT5 {side} {symbol}: {e}")
            return None
    
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """Place un ordre limite"""
        try:
            if not self.connected:
                return None
            
            order_type = mt5.ORDER_TYPE_BUY_LIMIT if side.lower() == 'buy' else mt5.ORDER_TYPE_SELL_LIMIT
            
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": amount,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Harmonic Bot Limit",
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erreur ordre limite MT5: {result.comment}")
                return None
            
            self.logger.trade_log(
                f"ORDRE_LIMITE_{side.upper()}", 
                symbol, 
                price, 
                amount,
                "Ordre limite MT5"
            )
            
            return {
                'id': result.order,
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'status': 'open'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur ordre limite MT5 {side} {symbol}: {e}")
            return None
    
    def place_stop_loss_order(self, symbol: str, side: str, amount: float, stop_price: float) -> Optional[Dict]:
        """Place un ordre stop loss"""
        try:
            if not self.connected:
                return None
            
            order_type = mt5.ORDER_TYPE_SELL_STOP if side.lower() == 'sell' else mt5.ORDER_TYPE_BUY_STOP
            
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": amount,
                "type": order_type,
                "price": stop_price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Harmonic Bot SL",
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erreur stop loss MT5: {result.comment}")
                return None
            
            self.logger.trade_log(
                f"STOP_LOSS_{side.upper()}", 
                symbol, 
                stop_price, 
                amount,
                "Stop loss MT5"
            )
            
            return {
                'id': result.order,
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': stop_price,
                'status': 'open'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur stop loss MT5 {side} {symbol}: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Annule un ordre"""
        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id),
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Ordre MT5 {order_id} annulé pour {symbol}")
                return True
            else:
                self.logger.error(f"Erreur annulation ordre MT5 {order_id}: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur annulation ordre MT5 {order_id}: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Récupère les ordres ouverts"""
        try:
            if not self.connected:
                return []
            
            orders = mt5.orders_get(symbol=symbol)
            if orders is None:
                return []
            
            result = []
            for order in orders:
                result.append({
                    'id': str(order.ticket),
                    'symbol': order.symbol,
                    'side': 'buy' if order.type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP] else 'sell',
                    'amount': order.volume_current,
                    'price': order.price_open,
                    'type': order.type,
                    'status': 'open'
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur récupération ordres ouverts MT5: {e}")
            return []
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Récupère les positions ouvertes"""
        try:
            if not self.connected:
                return []
            
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.symbol,
                    'size': pos.volume,
                    'side': 'long' if pos.type == mt5.POSITION_TYPE_BUY else 'short',
                    'unrealizedPnl': pos.profit,
                    'percentage': 0,  # À calculer si nécessaire
                    'price_open': pos.price_open,
                    'price_current': pos.price_current
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur récupération positions MT5: {e}")
            return []
    
    def update_balance(self):
        """Met à jour le solde du compte"""
        try:
            if not self.connected:
                return
            
            account_info = mt5.account_info()
            if account_info:
                self.balance = {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                    'currency': account_info.currency
                }
                
                self.logger.info(f"Balance MT5: {account_info.balance} {account_info.currency}")
                self.logger.info(f"Équité: {account_info.equity} {account_info.currency}")
                
        except Exception as e:
            self.logger.error(f"Erreur mise à jour solde MT5: {e}")
    
    def get_available_balance(self, currency: str = None) -> float:
        """Retourne le solde disponible"""
        try:
            return self.balance.get('free_margin', 0)
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
            symbol_info = self.get_symbol_info(symbol)
            tick = mt5.symbol_info_tick(symbol)
            
            if not symbol_info or not tick:
                return {}
            
            return {
                'symbol': symbol,
                'min_amount': symbol_info.get('min_lot', 0.01),
                'max_amount': symbol_info.get('max_lot', 100.0),
                'amount_precision': 2,  # Généralement 2 décimales pour les lots
                'price_precision': symbol_info.get('digits', 5),
                'current_price': tick.last,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': symbol_info.get('spread', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur info marché MT5 {symbol}: {e}")
            return {}
    
    def close_position(self, symbol: str, amount: float = None) -> Optional[Dict]:
        """Ferme une position"""
        try:
            if not self.connected:
                return None
            
            positions = self.get_positions(symbol)
            if not positions:
                self.logger.warning(f"Aucune position à fermer pour {symbol}")
                return None
            
            position = positions[0]
            close_amount = amount if amount else position['size']
            
            # Déterminer le côté opposé pour fermer
            close_side = 'sell' if position['side'] == 'long' else 'buy'
            
            # Fermer avec un ordre au marché
            order = self.place_market_order(symbol, close_side, close_amount)
            
            if order:
                self.logger.trade_log(
                    "FERMETURE_POSITION", 
                    symbol, 
                    order.get('price', 0), 
                    close_amount,
                    "Fermeture automatique MT5"
                )
            
            return order
            
        except Exception as e:
            self.logger.error(f"Erreur fermeture position MT5 {symbol}: {e}")
            return None
