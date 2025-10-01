import asyncio
import telegram
from telegram import Bot
from config import Config
from utils.logger import TradingLogger

class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.logger = TradingLogger()
    
    async def send_message(self, message):
        """Envoie un message Telegram"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='HTML')
            self.logger.debug(f"Message Telegram envoyé: {message}")
        except Exception as e:
            self.logger.error(f"Erreur envoi Telegram: {e}")
    
    async def notify_pattern_detected(self, pattern_type, symbol, points, confidence):
        """Notification de détection de pattern"""
        message = f"""
🔍 <b>PATTERN DÉTECTÉ</b>
📊 Type: {pattern_type}
💱 Symbole: {symbol}
📈 Points: {points}
🎯 Confiance: {confidence}%
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    async def notify_entry_zone(self, symbol, zone_type, price, direction):
        """Notification de zone d'entrée détectée"""
        direction_emoji = "🟢" if direction == "BUY" else "🔴"
        message = f"""
{direction_emoji} <b>ZONE D'ENTRÉE DÉTECTÉE</b>
💱 Symbole: {symbol}
📍 Zone: {zone_type}
💰 Prix: {price}
📊 Direction: {direction}
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    async def notify_trade_entry(self, symbol, direction, price, quantity, stop_loss, take_profit):
        """Notification d'entrée en position"""
        direction_emoji = "🟢" if direction == "BUY" else "🔴"
        message = f"""
{direction_emoji} <b>ENTRÉE EN POSITION</b>
💱 Symbole: {symbol}
📊 Direction: {direction}
💰 Prix d'entrée: {price}
📦 Quantité: {quantity}
🛑 Stop Loss: {stop_loss}
🎯 Take Profit: {take_profit}
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    async def notify_trade_exit(self, symbol, direction, entry_price, exit_price, quantity, pnl, reason):
        """Notification de sortie de position"""
        pnl_emoji = "💚" if pnl >= 0 else "❌"
        message = f"""
{pnl_emoji} <b>SORTIE DE POSITION</b>
💱 Symbole: {symbol}
📊 Direction: {direction}
💰 Prix d'entrée: {entry_price}
💰 Prix de sortie: {exit_price}
📦 Quantité: {quantity}
💵 PnL: {pnl:.2f} USDT
📝 Raison: {reason}
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    async def notify_analysis_update(self, symbol, status, details):
        """Notification de mise à jour d'analyse"""
        message = f"""
📊 <b>ANALYSE - {symbol}</b>
🔄 Statut: {status}
📋 Détails: {details}
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    async def notify_error(self, error_type, description):
        """Notification d'erreur"""
        message = f"""
⚠️ <b>ERREUR ROBOT</b>
🔧 Type: {error_type}
📝 Description: {description}
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    async def notify_bot_status(self, status, active_positions, daily_pnl):
        """Notification de statut du bot"""
        status_emoji = "🟢" if status == "ACTIF" else "🔴"
        message = f"""
{status_emoji} <b>STATUT DU ROBOT</b>
🔄 État: {status}
📊 Positions actives: {active_positions}
💵 PnL journalier: {daily_pnl:.2f} USDT
⏰ {self._get_timestamp()}
        """
        await self.send_message(message)
    
    def _get_timestamp(self):
        """Retourne le timestamp formaté"""
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    def send_sync(self, message):
        """Version synchrone pour envoyer un message"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.send_message(message))
        except RuntimeError:
            # Si pas de loop, en créer un nouveau
            asyncio.run(self.send_message(message))
