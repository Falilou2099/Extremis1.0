import logging
import os
from datetime import datetime
from config import Config

class TradingLogger:
    def __init__(self):
        self.setup_logger()
    
    def setup_logger(self):
        # Créer le dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configuration du logger
        self.logger = logging.getLogger('HarmonicBot')
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler pour fichier
        file_handler = logging.FileHandler(f'logs/{Config.LOG_FILE}')
        file_handler.setFormatter(formatter)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def trade_log(self, action, symbol, price, quantity, reason=""):
        """Log spécifique pour les trades"""
        message = f"TRADE - {action} | {symbol} | Prix: {price} | Quantité: {quantity}"
        if reason:
            message += f" | Raison: {reason}"
        self.info(message)
    
    def pattern_log(self, pattern_type, symbol, points, confidence):
        """Log spécifique pour la détection de patterns"""
        message = f"PATTERN - {pattern_type} détecté sur {symbol} | Points: {points} | Confiance: {confidence}%"
        self.info(message)
