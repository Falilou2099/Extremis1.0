import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from utils.logger import TradingLogger

class ConfirmationSystem:
    def __init__(self):
        self.logger = TradingLogger()
        
    def check_entry_confirmations(self, df_1h: pd.DataFrame, df_5m: pd.DataFrame, 
                                 pattern: Dict, zones: Dict) -> Dict:
        """Vérifie toutes les confirmations d'entrée selon la stratégie"""
        confirmations = {
            'candle_5m_confirmation': False,
            'trendline_break': False,
            'zone_break': False,
            'total_score': 0,
            'entry_signal': False,
            'entry_direction': None,
            'entry_price': None
        }
        
        # 1. Confirmation bougie 5 minutes au-delà du niveau 0.886
        candle_conf = self._check_5m_candle_confirmation(df_5m, zones)
        confirmations['candle_5m_confirmation'] = candle_conf['confirmed']
        if candle_conf['confirmed']:
            confirmations['total_score'] += 1
            confirmations['entry_price'] = candle_conf['close_price']
        
        # 2. Confirmation trendline avec 3 rebonds minimum
        trendline_conf = self._check_trendline_confirmation(df_1h, df_5m, pattern, zones)
        confirmations['trendline_break'] = trendline_conf['break_confirmed']
        if trendline_conf['break_confirmed']:
            confirmations['total_score'] += 1
        
        # 3. Confirmation cassure de zone (D à 0.886)
        zone_conf = self._check_zone_break_confirmation(df_5m, zones)
        confirmations['zone_break'] = zone_conf['zone_broken']
        if zone_conf['zone_broken']:
            confirmations['total_score'] += 1
        
        # Signal d'entrée si toutes les confirmations sont OK
        if confirmations['total_score'] >= 3:
            confirmations['entry_signal'] = True
            confirmations['entry_direction'] = 'SELL' if pattern['direction'] == 'bearish' else 'BUY'
            
            if not confirmations['entry_price']:
                confirmations['entry_price'] = df_5m.iloc[-1]['close']
        
        return confirmations
    
    def _check_5m_candle_confirmation(self, df_5m: pd.DataFrame, zones: Dict) -> Dict:
        """Vérifie la clôture d'une bougie 5m au-delà du niveau 0.886"""
        if len(df_5m) < 2:
            return {'confirmed': False, 'close_price': None}
        
        last_candle = df_5m.iloc[-1]
        fib_886 = zones.get('fib_886')
        direction = zones.get('direction')
        
        if not fib_886 or not direction:
            return {'confirmed': False, 'close_price': None}
        
        confirmed = False
        
        if direction == 'bearish':
            # Pattern bearish: clôture en dessous de 0.886
            confirmed = last_candle['close'] < fib_886
        else:
            # Pattern bullish: clôture au-dessus de 0.886
            confirmed = last_candle['close'] > fib_886
        
        return {
            'confirmed': confirmed,
            'close_price': last_candle['close'],
            'level_886': fib_886,
            'direction': direction
        }
    
    def _check_trendline_confirmation(self, df_1h: pd.DataFrame, df_5m: pd.DataFrame, 
                                    pattern: Dict, zones: Dict) -> Dict:
        """Vérifie la cassure de trendline avec minimum 3 rebonds"""
        
        # Construire la trendline basée sur les points du pattern
        trendline_data = self._build_trendline(df_1h, pattern)
        
        if not trendline_data or trendline_data['touches'] < 3:
            return {
                'break_confirmed': False,
                'touches': trendline_data['touches'] if trendline_data else 0,
                'reason': 'Pas assez de touches sur la trendline'
            }
        
        # Vérifier la cassure sur le timeframe 5m
        break_confirmed = self._check_trendline_break(df_5m, trendline_data, pattern['direction'])
        
        return {
            'break_confirmed': break_confirmed,
            'touches': trendline_data['touches'],
            'trendline_price': trendline_data.get('current_price'),
            'slope': trendline_data.get('slope')
        }
    
    def _build_trendline(self, df: pd.DataFrame, pattern: Dict) -> Optional[Dict]:
        """Construit une trendline basée sur les points du pattern"""
        points = pattern['points']
        direction = pattern['direction']
        
        # Collecter les points appropriés pour la trendline
        trendline_points = []
        
        if direction == 'bearish':
            # Trendline de résistance (hauts)
            for point_name in ['X', 'B', 'D']:
                point = points[point_name]
                if point['type'] == 'high':
                    trendline_points.append({
                        'index': point['index'],
                        'price': point['price'],
                        'timestamp': point['timestamp']
                    })
        else:
            # Trendline de support (bas)
            for point_name in ['X', 'B', 'D']:
                point = points[point_name]
                if point['type'] == 'low':
                    trendline_points.append({
                        'index': point['index'],
                        'price': point['price'],
                        'timestamp': point['timestamp']
                    })
        
        if len(trendline_points) < 2:
            return None
        
        # Calculer la pente et l'ordonnée à l'origine
        slope, intercept = self._calculate_trendline_equation(trendline_points)
        
        # Prix actuel de la trendline
        current_index = len(df) - 1
        current_trendline_price = slope * current_index + intercept
        
        # Compter les touches supplémentaires
        total_touches = self._count_trendline_touches(df, slope, intercept, direction)
        
        return {
            'slope': slope,
            'intercept': intercept,
            'touches': total_touches,
            'current_price': current_trendline_price,
            'points': trendline_points
        }
    
    def _calculate_trendline_equation(self, points: List[Dict]) -> Tuple[float, float]:
        """Calcule l'équation de la trendline (y = mx + b)"""
        x_values = [p['index'] for p in points]
        y_values = [p['price'] for p in points]
        
        # Régression linéaire
        n = len(points)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0, sum_y / n
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept
    
    def _count_trendline_touches(self, df: pd.DataFrame, slope: float, 
                               intercept: float, direction: str, tolerance: float = 0.002) -> int:
        """Compte le nombre de touches sur la trendline"""
        touches = 0
        
        for i in range(len(df)):
            trendline_price = slope * i + intercept
            candle = df.iloc[i]
            
            if direction == 'bearish':
                # Trendline de résistance
                if abs(candle['high'] - trendline_price) / trendline_price <= tolerance:
                    touches += 1
            else:
                # Trendline de support
                if abs(candle['low'] - trendline_price) / trendline_price <= tolerance:
                    touches += 1
        
        return touches
    
    def _check_trendline_break(self, df_5m: pd.DataFrame, trendline_data: Dict, direction: str) -> bool:
        """Vérifie si la trendline a été cassée sur le 5m"""
        if len(df_5m) < 1:
            return False
        
        last_candle = df_5m.iloc[-1]
        
        # Calculer le prix de la trendline au moment actuel
        # Note: il faudrait ajuster l'index pour correspondre au timeframe 5m
        current_trendline_price = trendline_data['current_price']
        
        if direction == 'bearish':
            # Cassure de résistance vers le haut
            return last_candle['close'] > current_trendline_price
        else:
            # Cassure de support vers le bas
            return last_candle['close'] < current_trendline_price
    
    def _check_zone_break_confirmation(self, df_5m: pd.DataFrame, zones: Dict) -> Dict:
        """Vérifie la cassure de la zone D à 0.886"""
        if len(df_5m) < 1:
            return {'zone_broken': False}
        
        last_candle = df_5m.iloc[-1]
        entry_zone = zones.get('entry_zone', {})
        direction = zones.get('direction')
        
        if not entry_zone or not direction:
            return {'zone_broken': False}
        
        zone_broken = False
        
        if direction == 'bearish':
            # Pour un pattern bearish, cassure vers le bas
            zone_broken = last_candle['close'] < entry_zone['lower']
        else:
            # Pour un pattern bullish, cassure vers le haut
            zone_broken = last_candle['close'] > entry_zone['upper']
        
        return {
            'zone_broken': zone_broken,
            'close_price': last_candle['close'],
            'zone_upper': entry_zone.get('upper'),
            'zone_lower': entry_zone.get('lower')
        }
    
    def get_stop_loss_level(self, pattern: Dict, zones: Dict, buffer_pips: int = 5) -> float:
        """Calcule le niveau de stop loss au-delà de la zone D"""
        d_point = pattern['points']['D']
        direction = pattern['direction']
        
        # Convertir les pips en prix (approximation pour les cryptos)
        pip_value = d_point['price'] * 0.0001 * buffer_pips
        
        if direction == 'bearish':
            # Stop loss au-dessus du point D
            return d_point['price'] + pip_value
        else:
            # Stop loss en dessous du point D
            return d_point['price'] - pip_value
    
    def get_take_profit_levels(self, pattern: Dict, zones: Dict) -> List[float]:
        """Calcule les niveaux de take profit aux zones de rebond"""
        targets = []
        
        # Niveaux Fibonacci comme cibles
        fib_levels = ['fib_618', 'fib_500', 'fib_382', 'fib_236']
        
        for level in fib_levels:
            if level in zones:
                targets.append(zones[level])
        
        # Point C comme cible principale
        c_point = pattern['points']['C']
        targets.append(c_point['price'])
        
        # Trier selon la direction
        if pattern['direction'] == 'bearish':
            targets.sort()  # Du plus bas au plus haut
        else:
            targets.sort(reverse=True)  # Du plus haut au plus bas
        
        return targets[:3]  # Maximum 3 niveaux de TP
