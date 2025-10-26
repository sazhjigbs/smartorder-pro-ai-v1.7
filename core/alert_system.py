"""
SmartOrder PRO - Alert System
Notifications Telegram et monitoring en temps réel
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

LOG = logging.getLogger("alert_system")
LOG.setLevel(logging.INFO)

class AlertLevel(Enum):
    """Niveaux d'alerte"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AlertType(Enum):
    """Types d'alerte"""
    TRADE_OPEN = "TRADE_OPEN"
    TRADE_CLOSE = "TRADE_CLOSE"
    PROFIT = "PROFIT"
    LOSS = "LOSS"
    DAILY_LIMIT = "DAILY_LIMIT"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    AI_SUGGESTION = "AI_SUGGESTION"
    WHALE_ACTIVITY = "WHALE_ACTIVITY"
    FLASH_CRASH = "FLASH_CRASH"
    ARBITRAGE = "ARBITRAGE"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class AlertSystem:
    """
    Système d'alertes multi-canal
    
    Canaux:
    - Telegram bot
    - Email
    - SMS (Twilio)
    - Discord webhook
    - Slack webhook
    - Desktop notification
    
    Features:
    - Filtrage par niveau
    - Formatage intelligent
    - Rate limiting
    - Alert history
    - Configurable triggers
    """
    
    def __init__(self):
        """Initialize Alert System"""
        # Configuration
        self.config = {
            'telegram': {
                'enabled': False,
                'bot_token': None,
                'chat_id': None
            },
            'email': {
                'enabled': False,
                'smtp_server': None,
                'smtp_port': 587,
                'username': None,
                'password': None,
                'to_address': None
            },
            'discord': {
                'enabled': False,
                'webhook_url': None
            },
            'slack': {
                'enabled': False,
                'webhook_url': None
            }
        }
        
        # Filtres d'alerte
        self.filters = {
            'min_level': AlertLevel.INFO,
            'enabled_types': [t for t in AlertType],
            'quiet_hours': {
                'enabled': False,
                'start': '23:00',
                'end': '07:00'
            }
        }
        
        # Historique
        self.alert_history = []
        self.max_history = 100
        
        # Rate limiting
        self.rate_limits = {
            'max_per_minute': 10,
            'max_per_hour': 50,
            'current_minute': 0,
            'current_hour': 0,
            'last_minute': datetime.now().minute,
            'last_hour': datetime.now().hour
        }
        
        # Stats
        self.stats = {
            'total_sent': 0,
            'by_channel': {},
            'by_type': {},
            'rate_limited': 0
        }
        
        LOG.info("AlertSystem initialized")
    
    def configure_telegram(self, bot_token: str, chat_id: str) -> bool:
        """Configure Telegram bot"""
        try:
            self.config['telegram']['bot_token'] = bot_token
            self.config['telegram']['chat_id'] = chat_id
            self.config['telegram']['enabled'] = True
            
            LOG.info("✅ Telegram configured")
            return True
        except Exception as e:
            LOG.error(f"Failed to configure Telegram: {e}")
            return False
    
    def send_alert(self, alert_type: AlertType, message: str, 
                   level: AlertLevel = AlertLevel.INFO, data: Dict = None) -> bool:
        """
        Envoie une alerte
        
        Args:
            alert_type: Type d'alerte
            message: Message de l'alerte
            level: Niveau d'importance
            data: Données supplémentaires (optionnel)
        """
        # Vérifier filtres
        if not self._should_send_alert(alert_type, level):
            return False
        
        # Vérifier rate limits
        if not self._check_rate_limit():
            self.stats['rate_limited'] += 1
            LOG.warning(f"Alert rate limited: {alert_type.value}")
            return False
        
        # Formater le message
        formatted_message = self._format_message(alert_type, message, level, data)
        
        # Envoyer sur tous les canaux actifs
        success = False
        
        if self.config['telegram']['enabled']:
            success = self._send_telegram(formatted_message) or success
        
        if self.config['discord']['enabled']:
            success = self._send_discord(formatted_message) or success
        
        if self.config['email']['enabled']:
            success = self._send_email(formatted_message, level) or success
        
        # Sauvegarder dans l'historique
        self._add_to_history(alert_type, message, level, formatted_message)
        
        # Update stats
        if success:
            self.stats['total_sent'] += 1
            self.stats['by_type'][alert_type.value] = \
                self.stats['by_type'].get(alert_type.value, 0) + 1
        
        return success
    
    def _should_send_alert(self, alert_type: AlertType, level: AlertLevel) -> bool:
        """Vérifie si l'alerte doit être envoyée"""
        # Check niveau minimum
        levels_order = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
        
        if levels_order.index(level) < levels_order.index(self.filters['min_level']):
            return False
        
        # Check type enabled
        if alert_type not in self.filters['enabled_types']:
            return False
        
        # Check quiet hours
        if self.filters['quiet_hours']['enabled']:
            # TODO: Implement quiet hours check
            pass
        
        return True
    
    def _check_rate_limit(self) -> bool:
        """Vérifie les rate limits"""
        now = datetime.now()
        
        # Reset counters si nouvelle minute/heure
        if now.minute != self.rate_limits['last_minute']:
            self.rate_limits['current_minute'] = 0
            self.rate_limits['last_minute'] = now.minute
        
        if now.hour != self.rate_limits['last_hour']:
            self.rate_limits['current_hour'] = 0
            self.rate_limits['last_hour'] = now.hour
        
        # Check limits
        if self.rate_limits['current_minute'] >= self.rate_limits['max_per_minute']:
            return False
        
        if self.rate_limits['current_hour'] >= self.rate_limits['max_per_hour']:
            return False
        
        # Increment counters
        self.rate_limits['current_minute'] += 1
        self.rate_limits['current_hour'] += 1
        
        return True
    
    def _format_message(self, alert_type: AlertType, message: str, 
                       level: AlertLevel, data: Dict = None) -> str:
        """Formate le message avec emojis et structure"""
        # Emojis par type
        emoji_map = {
            AlertType.TRADE_OPEN: "🚀",
            AlertType.TRADE_CLOSE: "✅",
            AlertType.PROFIT: "💰",
            AlertType.LOSS: "❌",
            AlertType.DAILY_LIMIT: "⚠️",
            AlertType.EMERGENCY_STOP: "🚨",
            AlertType.AI_SUGGESTION: "🤖",
            AlertType.WHALE_ACTIVITY: "🐋",
            AlertType.FLASH_CRASH: "⚡",
            AlertType.ARBITRAGE: "💎",
            AlertType.SYSTEM_ERROR: "🔴"
        }
        
        emoji = emoji_map.get(alert_type, "📢")
        
        # En-tête
        header = f"{emoji} *{alert_type.value}* ({level.value})\n"
        header += "─" * 30 + "\n\n"
        
        # Message principal
        body = f"{message}\n\n"
        
        # Données supplémentaires
        if data:
            body += "📊 *Details:*\n"
            for key, value in data.items():
                body += f"   • {key}: {value}\n"
            body += "\n"
        
        # Footer
        footer = f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return header + body + footer
    
    def _send_telegram(self, message: str) -> bool:
        """Envoie via Telegram"""
        try:
            # TODO: Implémenter avec python-telegram-bot
            # import telegram
            # bot = telegram.Bot(token=self.config['telegram']['bot_token'])
            # bot.send_message(
            #     chat_id=self.config['telegram']['chat_id'],
            #     text=message,
            #     parse_mode='Markdown'
            # )
            
            LOG.info(f"📱 Telegram sent: {message[:50]}...")
            self.stats['by_channel']['telegram'] = \
                self.stats['by_channel'].get('telegram', 0) + 1
            return True
            
        except Exception as e:
            LOG.error(f"Failed to send Telegram: {e}")
            return False
    
    def _send_discord(self, message: str) -> bool:
        """Envoie via Discord webhook"""
        try:
            # TODO: Implémenter avec requests
            # import requests
            # requests.post(
            #     self.config['discord']['webhook_url'],
            #     json={'content': message}
            # )
            
            LOG.info(f"💬 Discord sent: {message[:50]}...")
            self.stats['by_channel']['discord'] = \
                self.stats['by_channel'].get('discord', 0) + 1
            return True
            
        except Exception as e:
            LOG.error(f"Failed to send Discord: {e}")
            return False
    
    def _send_email(self, message: str, level: AlertLevel) -> bool:
        """Envoie via Email"""
        try:
            # TODO: Implémenter avec smtplib
            # import smtplib
            # from email.mime.text import MIMEText
            
            LOG.info(f"📧 Email sent: {message[:50]}...")
            self.stats['by_channel']['email'] = \
                self.stats['by_channel'].get('email', 0) + 1
            return True
            
        except Exception as e:
            LOG.error(f"Failed to send Email: {e}")
            return False
    
    def _add_to_history(self, alert_type: AlertType, message: str, 
                       level: AlertLevel, formatted: str):
        """Ajoute l'alerte à l'historique"""
        self.alert_history.append({
            'type': alert_type.value,
            'level': level.value,
            'message': message,
            'formatted': formatted,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limiter la taille de l'historique
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Retourne l'historique des alertes"""
        return self.alert_history[-limit:]
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        return {
            **self.stats,
            'history_size': len(self.alert_history),
            'rate_limits': {
                'per_minute': f"{self.rate_limits['current_minute']}/{self.rate_limits['max_per_minute']}",
                'per_hour': f"{self.rate_limits['current_hour']}/{self.rate_limits['max_per_hour']}"
            }
        }


# Instance globale
_alert_system = None

def get_alert_system() -> AlertSystem:
    """Récupère l'instance singleton"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system


# Fonctions helper
def alert_trade_open(symbol: str, side: str, price: float, size: float):
    """Alerte d'ouverture de trade"""
    system = get_alert_system()
    message = f"Position opened: {symbol} {side}"
    data = {
        'Entry Price': f'${price:,.2f}',
        'Size': f'${size:,.2f}'
    }
    system.send_alert(AlertType.TRADE_OPEN, message, AlertLevel.INFO, data)

def alert_trade_close(symbol: str, pnl: float, pnl_pct: float):
    """Alerte de fermeture de trade"""
    system = get_alert_system()
    level = AlertLevel.INFO if pnl > 0 else AlertLevel.WARNING
    alert_type = AlertType.PROFIT if pnl > 0 else AlertType.LOSS
    
    message = f"Position closed: {symbol}"
    data = {
        'PnL': f'${pnl:,.2f}',
        'PnL %': f'{pnl_pct:+.2f}%'
    }
    system.send_alert(alert_type, message, level, data)

def alert_emergency_stop(reason: str):
    """Alerte d'arrêt d'urgence"""
    system = get_alert_system()
    system.send_alert(
        AlertType.EMERGENCY_STOP,
        f"EMERGENCY STOP ACTIVATED: {reason}",
        AlertLevel.CRITICAL
    )

def alert_ai_suggestion(symbol: str, side: str, confidence: int):
    """Alerte de suggestion IA"""
    system = get_alert_system()
    message = f"AI suggests {side} {symbol}"
    data = {'Confidence': f'{confidence}%'}
    system.send_alert(AlertType.AI_SUGGESTION, message, AlertLevel.INFO, data)


if __name__ == "__main__":
    print("=" * 60)
    print("Alert System - Test")
    print("=" * 60)
    
    system = AlertSystem()
    
    # Test différents types d'alertes
    print("\n🧪 Testing alerts...")
    
    # Trade open
    system.send_alert(
        AlertType.TRADE_OPEN,
        "BTC LONG opened",
        AlertLevel.INFO,
        {'Entry': '$67,250', 'Size': '$5,000'}
    )
    
    # Profit
    system.send_alert(
        AlertType.PROFIT,
        "BTC position closed with profit",
        AlertLevel.INFO,
        {'PnL': '+$250', 'PnL %': '+5.0%'}
    )
    
    # AI Suggestion
    system.send_alert(
        AlertType.AI_SUGGESTION,
        "ETH LONG recommended",
        AlertLevel.INFO,
        {'Confidence': '85%', 'Entry': '$3,500'}
    )
    
    # Warning
    system.send_alert(
        AlertType.DAILY_LIMIT,
        "Daily loss limit approaching",
        AlertLevel.WARNING,
        {'Current': '-4.5%', 'Limit': '-5.0%'}
    )
    
    # Emergency
    system.send_alert(
        AlertType.EMERGENCY_STOP,
        "Emergency stop activated",
        AlertLevel.CRITICAL
    )
    
    # History
    print(f"\n📋 Alert History:")
    history = system.get_history(limit=5)
    
    for alert in history:
        print(f"   {alert['type']}: {alert['message'][:40]}...")
    
    # Stats
    stats = system.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Total sent: {stats['total_sent']}")
    print(f"   By type: {stats['by_type']}")
    print(f"   Rate limited: {stats['rate_limited']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
