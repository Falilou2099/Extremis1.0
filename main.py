#!/usr/bin/env python3
"""
Robot de Trading Harmonique Automatique
Basé sur la stratégie des patterns harmoniques avec notifications Telegram
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List

from config import Config
from utils.logger import TradingLogger
from utils.telegram_notifier import TelegramNotifier
from patterns.harmonic_detector import HarmonicPatternDetector
from patterns.zone_manager import ZoneManager
from trading.confirmation_system import ConfirmationSystem
from trading.connector_factory import ConnectorFactory
from trading.position_manager import PositionManager

class HarmonicTradingBot:
    def __init__(self):
        self.logger = TradingLogger()
        self.telegram = TelegramNotifier()
        self.pattern_detector = HarmonicPatternDetector()
        self.zone_manager = ZoneManager()
        self.confirmation_system = ConfirmationSystem()
        
        # Connexions trading - utiliser la factory pour le bon connecteur
        self.exchange = ConnectorFactory.create_connector()
        self.position_manager = PositionManager(self.exchange)
        
        # Afficher les informations de la plateforme
        platform_info = ConnectorFactory.get_platform_info()
        self.logger.info(f"Plateforme: {platform_info['platform'].upper()}")
        self.logger.info(f"Type de compte: {platform_info['account_type'].upper()}")
        self.logger.info(f"Symbole par défaut: {platform_info['symbol_default']}")
        
        # État du bot
        self.is_running = False
        self.last_analysis_time = None
        self.detected_patterns = {}
        
        self.logger.info("Robot de trading harmonique initialisé")
    
    async def start(self):
        """Démarre le robot de trading"""
        try:
            self.is_running = True
            
            # Notification de démarrage
            await self.telegram.notify_bot_status(
                "DÉMARRAGE", 
                self.position_manager.get_active_positions_count(),
                self.position_manager.get_daily_pnl()
            )
            
            self.logger.info("🚀 Robot de trading harmonique démarré")
            
            # Planifier les tâches
            self._schedule_tasks()
            
            # Boucle principale
            while self.is_running:
                try:
                    # Exécuter les tâches planifiées
                    schedule.run_pending()
                    
                    # Surveillance des positions
                    await self.position_manager.monitor_positions()
                    
                    # Attendre avant la prochaine itération
                    await asyncio.sleep(10)  # 10 secondes
                    
                except KeyboardInterrupt:
                    self.logger.info("Arrêt demandé par l'utilisateur")
                    break
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle principale: {e}")
                    await asyncio.sleep(30)  # Attendre plus longtemps en cas d'erreur
            
        except Exception as e:
            self.logger.error(f"Erreur critique au démarrage: {e}")
            await self.telegram.notify_error("DEMARRAGE", str(e))
        finally:
            await self.stop()
    
    def _schedule_tasks(self):
        """Planifie les tâches récurrentes"""
        # Analyse des patterns toutes les 5 minutes
        schedule.every(5).minutes.do(self._run_async_task, self.analyze_market)
        
        # Mise à jour du solde toutes les heures
        schedule.every().hour.do(self._run_async_task, self.update_account_info)
        
        # Nettoyage quotidien
        schedule.every().day.at("00:00").do(self._run_async_task, self.daily_cleanup)
        
        # Rapport de statut toutes les 4 heures
        schedule.every(4).hours.do(self._run_async_task, self.send_status_report)
    
    def _run_async_task(self, coro):
        """Exécute une coroutine dans la boucle d'événements"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(coro())
            else:
                loop.run_until_complete(coro())
        except Exception as e:
            self.logger.error(f"Erreur exécution tâche async: {e}")
    
    async def analyze_market(self):
        """Analyse complète du marché"""
        try:
            self.logger.info("🔍 Début de l'analyse du marché")
            
            symbol = Config.SYMBOL
            
            # Récupérer les données historiques
            df_1h = self.exchange.get_historical_data(symbol, Config.TIMEFRAME_MAIN, 200)
            df_5m = self.exchange.get_historical_data(symbol, Config.TIMEFRAME_ENTRY, 100)
            
            if df_1h.empty or df_5m.empty:
                self.logger.warning("Données insuffisantes pour l'analyse")
                return
            
            # Détecter les patterns harmoniques
            patterns = self.pattern_detector.detect_patterns(df_1h)
            
            for pattern in patterns:
                await self._process_pattern(pattern, df_1h, df_5m)
            
            self.last_analysis_time = datetime.now()
            
            # Notification d'analyse
            await self.telegram.notify_analysis_update(
                symbol, 
                f"{len(patterns)} patterns détectés",
                f"Dernière analyse: {self.last_analysis_time.strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            self.logger.error(f"Erreur analyse marché: {e}")
            await self.telegram.notify_error("ANALYSE_MARCHE", str(e))
    
    async def _process_pattern(self, pattern: Dict, df_1h: pd.DataFrame, df_5m: pd.DataFrame):
        """Traite un pattern détecté"""
        try:
            pattern_id = f"{pattern['type']}_{pattern['completion_time']}"
            
            # Éviter de retraiter le même pattern
            if pattern_id in self.detected_patterns:
                return
            
            self.logger.info(f"📊 Traitement du pattern {pattern['type']} (confiance: {pattern['confidence']:.1f}%)")
            
            # Créer les zones Fibonacci
            zones = self.zone_manager.create_fibonacci_zones(pattern)
            
            # Notification de pattern détecté
            await self.telegram.notify_pattern_detected(
                pattern['type'],
                Config.SYMBOL,
                f"D:{pattern['points']['D']['price']:.4f}",
                pattern['confidence']
            )
            
            # Vérifier les confirmations d'entrée
            confirmations = self.confirmation_system.check_entry_confirmations(
                df_1h, df_5m, pattern, zones
            )
            
            # Enregistrer le pattern
            self.detected_patterns[pattern_id] = {
                'pattern': pattern,
                'zones': zones,
                'detection_time': datetime.now(),
                'processed': False
            }
            
            # Si signal d'entrée confirmé
            if confirmations['entry_signal']:
                await self._handle_entry_signal(pattern, zones, confirmations)
            else:
                # Notification de zone d'entrée détectée (en attente)
                await self.telegram.notify_entry_zone(
                    Config.SYMBOL,
                    f"Zone 0.886: {zones.get('fib_886', 0):.4f}",
                    zones.get('fib_886', 0),
                    'BUY' if pattern['direction'] == 'bullish' else 'SELL'
                )
        
        except Exception as e:
            self.logger.error(f"Erreur traitement pattern: {e}")
    
    async def _handle_entry_signal(self, pattern: Dict, zones: Dict, confirmations: Dict):
        """Gère un signal d'entrée confirmé"""
        try:
            # Vérifier les limites de positions
            active_positions = self.position_manager.get_active_positions_count()
            
            if active_positions >= Config.MAX_POSITIONS:
                self.logger.warning(f"Limite de positions atteinte ({Config.MAX_POSITIONS})")
                return
            
            # Exécuter l'entrée
            success = await self.position_manager.execute_entry_signal(
                pattern, zones, confirmations
            )
            
            if success:
                self.logger.info("✅ Position ouverte avec succès")
                
                # Marquer le pattern comme traité
                pattern_id = f"{pattern['type']}_{pattern['completion_time']}"
                if pattern_id in self.detected_patterns:
                    self.detected_patterns[pattern_id]['processed'] = True
            else:
                self.logger.warning("❌ Échec de l'ouverture de position")
        
        except Exception as e:
            self.logger.error(f"Erreur gestion signal d'entrée: {e}")
            await self.telegram.notify_error("SIGNAL_ENTREE", str(e))
    
    async def update_account_info(self):
        """Met à jour les informations du compte"""
        try:
            self.exchange.update_balance()
            # Adapter selon la plateforme
            currency = 'USD' if Config.TRADING_PLATFORM.lower() == 'mt5' else 'USDT'
            balance = self.exchange.get_available_balance(currency)
            
            self.logger.info(f"💰 Solde {currency}: {balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour compte: {e}")
    
    async def daily_cleanup(self):
        """Nettoyage quotidien"""
        try:
            # Nettoyer les anciennes positions
            self.position_manager.cleanup_old_positions()
            
            # Nettoyer les anciennes zones
            self.zone_manager.cleanup_old_zones()
            
            # Nettoyer les anciens patterns
            self._cleanup_old_patterns()
            
            self.logger.info("🧹 Nettoyage quotidien effectué")
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage quotidien: {e}")
    
    def _cleanup_old_patterns(self, max_age_hours: int = 48):
        """Nettoie les anciens patterns"""
        current_time = datetime.now()
        patterns_to_remove = []
        
        for pattern_id, pattern_data in self.detected_patterns.items():
            age = (current_time - pattern_data['detection_time']).total_seconds() / 3600
            if age > max_age_hours:
                patterns_to_remove.append(pattern_id)
        
        for pattern_id in patterns_to_remove:
            del self.detected_patterns[pattern_id]
    
    async def send_status_report(self):
        """Envoie un rapport de statut"""
        try:
            active_positions = self.position_manager.get_active_positions_count()
            daily_pnl = self.position_manager.get_daily_pnl()
            
            await self.telegram.notify_bot_status(
                "ACTIF" if self.is_running else "INACTIF",
                active_positions,
                daily_pnl
            )
            
        except Exception as e:
            self.logger.error(f"Erreur rapport de statut: {e}")
    
    async def stop(self):
        """Arrête le robot de trading"""
        try:
            self.is_running = False
            
            # Fermer toutes les positions si demandé
            # await self.position_manager.close_all_positions("Arrêt du robot")
            
            # Notification d'arrêt
            await self.telegram.notify_bot_status(
                "ARRÊTÉ",
                self.position_manager.get_active_positions_count(),
                self.position_manager.get_daily_pnl()
            )
            
            self.logger.info("🛑 Robot de trading harmonique arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt: {e}")

def main():
    """Point d'entrée principal"""
    try:
        # Créer et démarrer le bot
        bot = HarmonicTradingBot()
        
        # Démarrer la boucle d'événements
        asyncio.run(bot.start())
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du robot demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

if __name__ == "__main__":
    main()
