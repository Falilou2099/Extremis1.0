import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from utils.logger import TradingLogger

class HarmonicPatternDetector:
    def __init__(self):
        self.logger = TradingLogger()
        
        # Ratios Fibonacci pour les patterns harmoniques
        self.butterfly_ratios = {
            'XA_AB': (0.786, 0.786),  # AB doit être 78.6% de XA
            'AB_BC': (0.382, 0.886),  # BC entre 38.2% et 88.6% de AB
            'BC_CD': (1.618, 2.618),  # CD entre 161.8% et 261.8% de BC
            'XA_AD': (1.27, 1.618)    # AD entre 127% et 161.8% de XA
        }
        
        self.tolerance = 0.05  # 5% de tolérance pour les ratios
    
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Détecte les patterns harmoniques dans les données OHLCV"""
        patterns = []
        
        if len(df) < 50:  # Besoin d'au moins 50 barres
            return patterns
        
        # Identifier les pivots (hauts et bas significatifs)
        pivots = self._find_pivots(df)
        
        if len(pivots) < 5:  # Besoin d'au moins 5 pivots pour X,A,B,C,D
            return patterns
        
        # Chercher des patterns butterfly
        butterfly_patterns = self._find_butterfly_patterns(df, pivots)
        patterns.extend(butterfly_patterns)
        
        return patterns
    
    def _find_pivots(self, df: pd.DataFrame, window: int = 5) -> List[Dict]:
        """Trouve les pivots (hauts et bas significatifs)"""
        pivots = []
        
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(window, len(df) - window):
            # Pivot haut
            if all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] >= highs[i+j] for j in range(1, window+1)):
                pivots.append({
                    'index': i,
                    'price': highs[i],
                    'type': 'high',
                    'timestamp': df.index[i]
                })
            
            # Pivot bas
            if all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] <= lows[i+j] for j in range(1, window+1)):
                pivots.append({
                    'index': i,
                    'price': lows[i],
                    'type': 'low',
                    'timestamp': df.index[i]
                })
        
        # Trier par index
        pivots.sort(key=lambda x: x['index'])
        return pivots
    
    def _find_butterfly_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict]:
        """Trouve les patterns butterfly"""
        patterns = []
        
        # Besoin d'au moins 5 pivots pour X,A,B,C,D
        for i in range(len(pivots) - 4):
            # Prendre 5 pivots consécutifs
            x, a, b, c, d = pivots[i:i+5]
            
            # Vérifier l'alternance haut/bas
            if not self._is_valid_sequence([x, a, b, c, d]):
                continue
            
            # Calculer les ratios
            ratios = self._calculate_ratios(x, a, b, c, d)
            
            # Vérifier si c'est un pattern butterfly
            if self._is_butterfly_pattern(ratios):
                pattern = {
                    'type': 'butterfly',
                    'points': {
                        'X': x,
                        'A': a,
                        'B': b,
                        'C': c,
                        'D': d
                    },
                    'ratios': ratios,
                    'confidence': self._calculate_confidence(ratios),
                    'direction': 'bearish' if d['type'] == 'high' else 'bullish',
                    'completion_time': d['timestamp']
                }
                patterns.append(pattern)
                
                self.logger.pattern_log(
                    'Butterfly', 
                    'SYMBOL', 
                    f"X:{x['price']:.4f}, A:{a['price']:.4f}, B:{b['price']:.4f}, C:{c['price']:.4f}, D:{d['price']:.4f}",
                    pattern['confidence']
                )
        
        return patterns
    
    def _is_valid_sequence(self, points: List[Dict]) -> bool:
        """Vérifie que la séquence de points alterne entre hauts et bas"""
        types = [p['type'] for p in points]
        
        # Pattern bullish: low-high-low-high-low
        # Pattern bearish: high-low-high-low-high
        
        bullish_pattern = ['low', 'high', 'low', 'high', 'low']
        bearish_pattern = ['high', 'low', 'high', 'low', 'high']
        
        return types == bullish_pattern or types == bearish_pattern
    
    def _calculate_ratios(self, x, a, b, c, d) -> Dict:
        """Calcule les ratios Fibonacci entre les points"""
        xa = abs(a['price'] - x['price'])
        ab = abs(b['price'] - a['price'])
        bc = abs(c['price'] - b['price'])
        cd = abs(d['price'] - c['price'])
        ad = abs(d['price'] - a['price'])
        
        ratios = {}
        
        if xa != 0:
            ratios['AB_XA'] = ab / xa
            ratios['AD_XA'] = ad / xa
        
        if ab != 0:
            ratios['BC_AB'] = bc / ab
        
        if bc != 0:
            ratios['CD_BC'] = cd / bc
        
        return ratios
    
    def _is_butterfly_pattern(self, ratios: Dict) -> bool:
        """Vérifie si les ratios correspondent à un pattern butterfly"""
        checks = []
        
        # AB doit être ~78.6% de XA
        if 'AB_XA' in ratios:
            ab_xa = ratios['AB_XA']
            checks.append(self._is_ratio_valid(ab_xa, 0.786, self.tolerance))
        
        # BC doit être entre 38.2% et 88.6% de AB
        if 'BC_AB' in ratios:
            bc_ab = ratios['BC_AB']
            checks.append(0.382 - self.tolerance <= bc_ab <= 0.886 + self.tolerance)
        
        # CD doit être entre 161.8% et 261.8% de BC
        if 'CD_BC' in ratios:
            cd_bc = ratios['CD_BC']
            checks.append(1.618 - self.tolerance <= cd_bc <= 2.618 + self.tolerance)
        
        # AD doit être entre 127% et 161.8% de XA
        if 'AD_XA' in ratios:
            ad_xa = ratios['AD_XA']
            checks.append(1.27 - self.tolerance <= ad_xa <= 1.618 + self.tolerance)
        
        # Au moins 3 ratios doivent être valides
        return sum(checks) >= 3
    
    def _is_ratio_valid(self, actual: float, expected: float, tolerance: float) -> bool:
        """Vérifie si un ratio est dans la tolérance acceptable"""
        return abs(actual - expected) <= tolerance
    
    def _calculate_confidence(self, ratios: Dict) -> float:
        """Calcule le niveau de confiance du pattern (0-100%)"""
        confidence_scores = []
        
        # Score pour chaque ratio
        if 'AB_XA' in ratios:
            score = max(0, 100 - abs(ratios['AB_XA'] - 0.786) * 100)
            confidence_scores.append(score)
        
        if 'BC_AB' in ratios:
            # Score basé sur la proximité avec les niveaux Fibonacci
            bc_ab = ratios['BC_AB']
            fib_levels = [0.382, 0.5, 0.618, 0.786, 0.886]
            min_distance = min(abs(bc_ab - level) for level in fib_levels)
            score = max(0, 100 - min_distance * 100)
            confidence_scores.append(score)
        
        if 'CD_BC' in ratios:
            cd_bc = ratios['CD_BC']
            target = 2.618 if cd_bc > 2.0 else 1.618
            score = max(0, 100 - abs(cd_bc - target) * 50)
            confidence_scores.append(score)
        
        if 'AD_XA' in ratios:
            ad_xa = ratios['AD_XA']
            target = 1.618 if ad_xa > 1.4 else 1.27
            score = max(0, 100 - abs(ad_xa - target) * 100)
            confidence_scores.append(score)
        
        return np.mean(confidence_scores) if confidence_scores else 0
    
    def get_fibonacci_zones(self, pattern: Dict) -> Dict:
        """Calcule les zones Fibonacci pour un pattern"""
        d_point = pattern['points']['D']
        c_point = pattern['points']['C']
        
        # Distance D-C
        dc_distance = abs(d_point['price'] - c_point['price'])
        
        zones = {}
        
        # Zone 0.886 (niveau clé pour la stratégie)
        if pattern['direction'] == 'bearish':
            zones['level_886'] = d_point['price'] - (dc_distance * 0.886)
            zones['entry_zone'] = (d_point['price'], zones['level_886'])
        else:
            zones['level_886'] = d_point['price'] + (dc_distance * 0.886)
            zones['entry_zone'] = (zones['level_886'], d_point['price'])
        
        # Autres niveaux Fibonacci
        for level in [0.236, 0.382, 0.5, 0.618, 0.786]:
            if pattern['direction'] == 'bearish':
                zones[f'level_{int(level*1000)}'] = d_point['price'] - (dc_distance * level)
            else:
                zones[f'level_{int(level*1000)}'] = d_point['price'] + (dc_distance * level)
        
        return zones
