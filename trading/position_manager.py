import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from config import Config
from utils.logger import TradingLogger
from utils.telegram_notifier import TelegramNotifier
from trading.exchange_connector import ExchangeConnector
import asyncio

class PositionManager:
    def __init__(self, exchange_connector: ExchangeConnector):
        self.logger = TradingLogger()
        self.telegram = TelegramNotifier()
        self.exchange = exchange_connector
        self.active_positions = {}
        self.pending_orders = {}
        
    async def execute_entry_signal(self, pattern: Dict, zones: Dict, confirmations: Dict) -> bool:
        """Exécute l'entrée en position basée sur le signal"""
        try:
            if not confirmations['entry_signal']:
                return False
            
            symbol = Config.SYMBOL
            direction = confirmations['entry_direction']
            entry_price = confirmations['entry_price']
            
            # Calculer les niveaux de stop loss et take profit
            stop_loss = self._calculate_stop_loss(pattern, zones)
            take_profits = self._calculate_take_profits(pattern, zones)
            
            # Calculer la taille de position
            position_size = self._calculate_position_size(entry_price, stop_loss)
            
            if position_size <= 0:
                self.logger.warning("Taille de position invalide")
                return False
            
            # Placer l'ordre d'entrée
            side = 'buy' if direction == 'BUY' else 'sell'
            entry_order = self.exchange.place_market_order(symbol, side, position_size)
            
            if not entry_order:
                await self.telegram.notify_error("ORDRE_ENTREE", "Échec de l'ordre d'entrée")
                return False
            
            # Créer la position
            position_id = f"{pattern['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            position = {
                'id': position_id,
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profits': take_profits,
                'entry_time': datetime.now(),
                'pattern': pattern,
                'zones': zones,
                'status': 'ACTIVE',
                'entry_order_id': entry_order.get('id'),
                'stop_order_id': None,
                'tp_orders': []
            }
            
            # Placer le stop loss
            await self._place_stop_loss(position)
            
            # Placer les take profits
            await self._place_take_profits(position)
            
            # Enregistrer la position
            self.active_positions[position_id] = position
            
            # Notification Telegram
            await self.telegram.notify_trade_entry(
                symbol, direction, entry_price, position_size, 
                stop_loss, take_profits[0] if take_profits else None
            )
            
            self.logger.trade_log(
                "ENTREE_POSITION", symbol, entry_price, position_size,
                f"Pattern: {pattern['type']}, Direction: {direction}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur exécution entrée: {e}")
            await self.telegram.notify_error("EXECUTION_ENTREE", str(e))
            return False
    
    def _calculate_stop_loss(self, pattern: Dict, zones: Dict) -> float:
        """Calcule le niveau de stop loss"""
        d_point = pattern['points']['D']
        direction = pattern['direction']
        
        # Buffer de sécurité (5 pips)
        buffer = d_point['price'] * 0.0005  # 0.05% comme buffer
        
        if direction == 'bearish':
            # Stop loss au-dessus du point D
            return d_point['price'] + buffer
        else:
            # Stop loss en dessous du point D
            return d_point['price'] - buffer
    
    def _calculate_take_profits(self, pattern: Dict, zones: Dict) -> List[float]:
        """Calcule les niveaux de take profit"""
        targets = []
        
        # Niveaux Fibonacci comme cibles
        fib_levels = ['fib_618', 'fib_500', 'fib_382']
        
        for level in fib_levels:
            if level in zones:
                targets.append(zones[level])
        
        # Point C comme cible finale
        c_point = pattern['points']['C']
        targets.append(c_point['price'])
        
        # Trier selon la direction
        if pattern['direction'] == 'bearish':
            targets.sort()  # Du plus bas au plus haut
        else:
            targets.sort(reverse=True)  # Du plus haut au plus bas
        
        return targets[:3]  # Maximum 3 niveaux
    
    def _calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """Calcule la taille de position basée sur le risque"""
        try:
            # Montant total disponible
            total_balance = self.exchange.get_available_balance('USDT')
            
            # Montant à risquer (1% par défaut)
            risk_amount = self.exchange.calculate_risk_amount(total_balance)
            
            # Calculer la taille de position
            position_size = self.exchange.calculate_position_size(
                Config.SYMBOL, risk_amount, entry_price, stop_loss
            )
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Erreur calcul taille position: {e}")
            return 0
    
    async def _place_stop_loss(self, position: Dict):
        """Place l'ordre de stop loss"""
        try:
            symbol = position['symbol']
            direction = position['direction']
            size = position['position_size']
            stop_price = position['stop_loss']
            
            # Side opposé pour le stop loss
            stop_side = 'sell' if direction == 'BUY' else 'buy'
            
            stop_order = self.exchange.place_stop_loss_order(
                symbol, stop_side, size, stop_price
            )
            
            if stop_order:
                position['stop_order_id'] = stop_order.get('id')
                self.logger.info(f"Stop loss placé: {stop_price}")
            
        except Exception as e:
            self.logger.error(f"Erreur placement stop loss: {e}")
    
    async def _place_take_profits(self, position: Dict):
        """Place les ordres de take profit"""
        try:
            symbol = position['symbol']
            direction = position['direction']
            total_size = position['position_size']
            take_profits = position['take_profits']
            
            # Side opposé pour les take profits
            tp_side = 'sell' if direction == 'BUY' else 'buy'
            
            # Diviser la position en parts égales
            tp_size = total_size / len(take_profits)
            
            for i, tp_price in enumerate(take_profits):
                tp_order = self.exchange.place_limit_order(
                    symbol, tp_side, tp_size, tp_price
                )
                
                if tp_order:
                    position['tp_orders'].append({
                        'order_id': tp_order.get('id'),
                        'price': tp_price,
                        'size': tp_size,
                        'level': i + 1
                    })
                    self.logger.info(f"Take profit {i+1} placé: {tp_price}")
        
        except Exception as e:
            self.logger.error(f"Erreur placement take profits: {e}")
    
    async def monitor_positions(self):
        """Surveille les positions actives"""
        for position_id, position in list(self.active_positions.items()):
            try:
                await self._check_position_status(position)
                await self._update_trailing_stop(position)
                
            except Exception as e:
                self.logger.error(f"Erreur monitoring position {position_id}: {e}")
    
    async def _check_position_status(self, position: Dict):
        """Vérifie le statut d'une position"""
        symbol = position['symbol']
        current_price = self.exchange.get_current_price(symbol)
        
        # Vérifier si les ordres ont été exécutés
        open_orders = self.exchange.get_open_orders(symbol)
        open_order_ids = [order['id'] for order in open_orders]
        
        # Vérifier les take profits
        for tp_order in position['tp_orders']:
            if tp_order['order_id'] not in open_order_ids:
                # Take profit exécuté
                await self._handle_take_profit_hit(position, tp_order, current_price)
        
        # Vérifier le stop loss
        if position['stop_order_id'] and position['stop_order_id'] not in open_order_ids:
            # Stop loss exécuté
            await self._handle_stop_loss_hit(position, current_price)
    
    async def _handle_take_profit_hit(self, position: Dict, tp_order: Dict, current_price: float):
        """Gère l'exécution d'un take profit"""
        try:
            # Calculer le PnL partiel
            entry_price = position['entry_price']
            tp_price = tp_order['price']
            size = tp_order['size']
            
            if position['direction'] == 'BUY':
                pnl = (tp_price - entry_price) * size
            else:
                pnl = (entry_price - tp_price) * size
            
            # Notification
            await self.telegram.notify_trade_exit(
                position['symbol'], position['direction'], 
                entry_price, tp_price, size, pnl,
                f"Take Profit {tp_order['level']} atteint"
            )
            
            self.logger.trade_log(
                "TAKE_PROFIT", position['symbol'], tp_price, size,
                f"TP{tp_order['level']} - PnL: {pnl:.2f}"
            )
            
            # Marquer comme exécuté
            tp_order['executed'] = True
            tp_order['execution_price'] = current_price
            
        except Exception as e:
            self.logger.error(f"Erreur gestion take profit: {e}")
    
    async def _handle_stop_loss_hit(self, position: Dict, current_price: float):
        """Gère l'exécution du stop loss"""
        try:
            # Calculer le PnL
            entry_price = position['entry_price']
            stop_price = position['stop_loss']
            size = position['position_size']
            
            if position['direction'] == 'BUY':
                pnl = (stop_price - entry_price) * size
            else:
                pnl = (entry_price - stop_price) * size
            
            # Notification
            await self.telegram.notify_trade_exit(
                position['symbol'], position['direction'],
                entry_price, stop_price, size, pnl,
                "Stop Loss atteint"
            )
            
            self.logger.trade_log(
                "STOP_LOSS", position['symbol'], stop_price, size,
                f"SL exécuté - PnL: {pnl:.2f}"
            )
            
            # Fermer la position
            position['status'] = 'CLOSED'
            position['close_reason'] = 'STOP_LOSS'
            position['close_time'] = datetime.now()
            
            # Annuler les ordres restants
            await self._cancel_remaining_orders(position)
            
        except Exception as e:
            self.logger.error(f"Erreur gestion stop loss: {e}")
    
    async def _update_trailing_stop(self, position: Dict):
        """Met à jour le trailing stop si configuré"""
        # Implémentation future pour trailing stop
        pass
    
    async def _cancel_remaining_orders(self, position: Dict):
        """Annule les ordres restants d'une position"""
        try:
            symbol = position['symbol']
            
            # Annuler les take profits restants
            for tp_order in position['tp_orders']:
                if not tp_order.get('executed', False):
                    self.exchange.cancel_order(tp_order['order_id'], symbol)
            
            # Annuler le stop loss si nécessaire
            if position['stop_order_id']:
                self.exchange.cancel_order(position['stop_order_id'], symbol)
                
        except Exception as e:
            self.logger.error(f"Erreur annulation ordres: {e}")
    
    async def close_all_positions(self, reason: str = "Fermeture manuelle"):
        """Ferme toutes les positions actives"""
        for position_id, position in list(self.active_positions.items()):
            if position['status'] == 'ACTIVE':
                await self._force_close_position(position, reason)
    
    async def _force_close_position(self, position: Dict, reason: str):
        """Force la fermeture d'une position"""
        try:
            symbol = position['symbol']
            size = position['position_size']
            
            # Annuler tous les ordres
            await self._cancel_remaining_orders(position)
            
            # Fermer au marché
            close_side = 'sell' if position['direction'] == 'BUY' else 'buy'
            close_order = self.exchange.place_market_order(symbol, close_side, size)
            
            if close_order:
                current_price = self.exchange.get_current_price(symbol)
                entry_price = position['entry_price']
                
                if position['direction'] == 'BUY':
                    pnl = (current_price - entry_price) * size
                else:
                    pnl = (entry_price - current_price) * size
                
                # Notification
                await self.telegram.notify_trade_exit(
                    symbol, position['direction'],
                    entry_price, current_price, size, pnl, reason
                )
                
                # Marquer comme fermée
                position['status'] = 'CLOSED'
                position['close_reason'] = reason
                position['close_time'] = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Erreur fermeture forcée: {e}")
    
    def get_active_positions_count(self) -> int:
        """Retourne le nombre de positions actives"""
        return len([p for p in self.active_positions.values() if p['status'] == 'ACTIVE'])
    
    def get_daily_pnl(self) -> float:
        """Calcule le PnL journalier"""
        today = datetime.now().date()
        daily_pnl = 0
        
        for position in self.active_positions.values():
            if position.get('close_time'):
                close_date = position['close_time'].date()
                if close_date == today:
                    # Calculer le PnL de cette position fermée
                    # (implémentation simplifiée)
                    pass
        
        return daily_pnl
    
    def cleanup_old_positions(self, days: int = 7):
        """Nettoie les anciennes positions fermées"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        positions_to_remove = []
        for position_id, position in self.active_positions.items():
            if (position['status'] == 'CLOSED' and 
                position.get('close_time') and 
                position['close_time'] < cutoff_date):
                positions_to_remove.append(position_id)
        
        for position_id in positions_to_remove:
            del self.active_positions[position_id]
        
        if positions_to_remove:
            self.logger.info(f"Nettoyage: {len(positions_to_remove)} anciennes positions supprimées")
