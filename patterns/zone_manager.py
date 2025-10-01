import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from utils.logger import TradingLogger

class ZoneManager:
    def __init__(self):
        self.logger = TradingLogger()
        self.active_zones = {}
        
    def create_fibonacci_zones(self, pattern: Dict) -> Dict:
        """Crée les zones Fibonacci basées sur le pattern harmonique"""
        d_point = pattern['points']['D']
        c_point = pattern['points']['C']
        
        # Distance D-C pour les retracements
        dc_distance = abs(d_point['price'] - c_point['price'])
        
        zones = {
            'pattern_id': f"{pattern['type']}_{d_point['timestamp']}",
            'direction': pattern['direction'],
            'base_price': d_point['price'],
            'target_price': c_point['price']
        }
        
        # Niveaux Fibonacci standard
        fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786, 0.886, 1.0]
        
        for level in fib_levels:
            if pattern['direction'] == 'bearish':
                # Pour un pattern bearish, les niveaux sont en dessous de D
                price_level = d_point['price'] - (dc_distance * level)
            else:
                # Pour un pattern bullish, les niveaux sont au-dessus de D
                price_level = d_point['price'] + (dc_distance * level)
            
            zones[f'fib_{int(level*1000)}'] = price_level
        
        # Zone critique 0.886 (zone d'entrée principale selon la stratégie)
        zones['entry_zone'] = {
            'upper': max(d_point['price'], zones['fib_886']),
            'lower': min(d_point['price'], zones['fib_886']),
            'is_active': True
        }
        
        # Zone de rebond (entre 0.886 et C)
        zones['rebound_zone'] = {
            'upper': max(zones['fib_886'], c_point['price']),
            'lower': min(zones['fib_886'], c_point['price']),
            'is_active': True
        }
        
        return zones
    
    def create_trendline_zones(self, df: pd.DataFrame, pattern: Dict) -> Dict:
        """Crée les zones basées sur les trendlines"""
        points = pattern['points']
        
        # Points pour tracer la trendline
        trendline_points = []
        
        if pattern['direction'] == 'bearish':
            # Trendline de résistance (hauts décroissants)
            for point_name in ['X', 'B', 'D']:
                if points[point_name]['type'] == 'high':
                    trendline_points.append({
                        'timestamp': points[point_name]['timestamp'],
                        'price': points[point_name]['price'],
                        'index': points[point_name]['index']
                    })
        else:
            # Trendline de support (bas croissants)
            for point_name in ['X', 'B', 'D']:
                if points[point_name]['type'] == 'low':
                    trendline_points.append({
                        'timestamp': points[point_name]['timestamp'],
                        'price': points[point_name]['price'],
                        'index': points[point_name]['index']
                    })
        
        if len(trendline_points) >= 2:
            # Calculer la pente de la trendline
            slope = self._calculate_trendline_slope(trendline_points)
            
            # Projeter la trendline vers le futur
            last_point = trendline_points[-1]
            current_index = len(df) - 1
            
            projected_price = last_point['price'] + slope * (current_index - last_point['index'])
            
            return {
                'slope': slope,
                'last_point': last_point,
                'projected_price': projected_price,
                'touches': len(trendline_points),
                'is_valid': len(trendline_points) >= 3  # Minimum 3 touches selon la stratégie
            }
        
        return None
    
    def _calculate_trendline_slope(self, points: List[Dict]) -> float:
        """Calcule la pente d'une trendline"""
        if len(points) < 2:
            return 0
        
        # Régression linéaire simple
        x_values = [p['index'] for p in points]
        y_values = [p['price'] for p in points]
        
        n = len(points)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def check_zone_breach(self, current_price: float, zones: Dict, timeframe_data: pd.DataFrame) -> Dict:
        """Vérifie si le prix a cassé une zone importante"""
        breaches = {
            'entry_zone_breach': False,
            'trendline_breach': False,
            'fib_886_breach': False,
            'confirmation_level': 0
        }
        
        # Vérifier la cassure de la zone d'entrée (D à 0.886)
        entry_zone = zones.get('entry_zone', {})
        if entry_zone.get('is_active', False):
            if entry_zone['lower'] <= current_price <= entry_zone['upper']:
                breaches['entry_zone_breach'] = True
                breaches['confirmation_level'] += 1
        
        # Vérifier la cassure du niveau 0.886
        fib_886 = zones.get('fib_886')
        if fib_886:
            tolerance = abs(fib_886 * 0.001)  # 0.1% de tolérance
            if abs(current_price - fib_886) <= tolerance:
                breaches['fib_886_breach'] = True
                breaches['confirmation_level'] += 1
        
        return breaches
    
    def check_candle_confirmation(self, df: pd.DataFrame, zones: Dict) -> bool:
        """Vérifie la confirmation par clôture de bougie au-delà du niveau 0.886"""
        if len(df) < 2:
            return False
        
        last_candle = df.iloc[-1]
        fib_886 = zones.get('fib_886')
        
        if not fib_886:
            return False
        
        # Vérifier si la bougie a clôturé au-delà du niveau 0.886
        direction = zones.get('direction')
        
        if direction == 'bearish':
            # Pour un pattern bearish, on cherche une clôture en dessous de 0.886
            return last_candle['close'] < fib_886
        else:
            # Pour un pattern bullish, on cherche une clôture au-dessus de 0.886
            return last_candle['close'] > fib_886
    
    def get_rebound_targets(self, zones: Dict) -> List[float]:
        """Retourne les niveaux de rebond potentiels pour les take profits"""
        targets = []
        
        # Niveaux Fibonacci comme cibles
        fib_levels = ['fib_618', 'fib_500', 'fib_382', 'fib_236']
        
        for level in fib_levels:
            if level in zones:
                targets.append(zones[level])
        
        # Ajouter le point C comme cible principale
        if 'target_price' in zones:
            targets.append(zones['target_price'])
        
        return sorted(targets, reverse=(zones.get('direction') == 'bearish'))
    
    def update_zone_status(self, zone_id: str, status: str):
        """Met à jour le statut d'une zone"""
        if zone_id in self.active_zones:
            self.active_zones[zone_id]['status'] = status
            self.active_zones[zone_id]['last_update'] = pd.Timestamp.now()
    
    def cleanup_old_zones(self, max_age_hours: int = 24):
        """Nettoie les zones anciennes"""
        current_time = pd.Timestamp.now()
        zones_to_remove = []
        
        for zone_id, zone_data in self.active_zones.items():
            if 'last_update' in zone_data:
                age = (current_time - zone_data['last_update']).total_seconds() / 3600
                if age > max_age_hours:
                    zones_to_remove.append(zone_id)
        
        for zone_id in zones_to_remove:
            del self.active_zones[zone_id]
            self.logger.info(f"Zone supprimée: {zone_id} (trop ancienne)")
    
    def get_active_zones(self) -> Dict:
        """Retourne toutes les zones actives"""
        return self.active_zones.copy()
