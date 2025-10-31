"""
Notification Manager
Multi-canal: Telegram, Slack, Email, SMS
"""
import time
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


@dataclass
class NotificationConfig:
    """Configuration des notifications"""
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    slack_webhook_url: Optional[str] = None
    
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    email_password: Optional[str] = None
    
    sms_api_key: Optional[str] = None
    sms_to: Optional[str] = None
    
    webhook_url: Optional[str] = None


@dataclass
class Notification:
    """Notification"""
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    timestamp: float = 0.0
    metadata: Optional[Dict] = None


class NotificationManager:
    """Gestionnaire de notifications multi-canal"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.notification_history: List[Notification] = []
        self.failed_notifications: List[Dict] = []
        
        # Rate limiting
        self.rate_limits = {
            NotificationPriority.LOW: 300,  # 5 min
            NotificationPriority.MEDIUM: 60,  # 1 min
            NotificationPriority.HIGH: 10,  # 10 sec
            NotificationPriority.CRITICAL: 0  # Immédiat
        }
        self.last_sent = {}
    
    async def send(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Envoie une notification"""
        
        if channels is None:
            channels = self._get_default_channels(priority)
        
        # Rate limiting
        if not self._can_send(priority):
            return {
                "sent": False,
                "reason": "Rate limit exceeded"
            }
        
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            channels=channels,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.notification_history.append(notification)
        
        # Envoyer sur tous les canaux
        results = {}
        for channel in channels:
            try:
                if channel == NotificationChannel.TELEGRAM:
                    success = await self._send_telegram(notification)
                elif channel == NotificationChannel.SLACK:
                    success = await self._send_slack(notification)
                elif channel == NotificationChannel.EMAIL:
                    success = await self._send_email(notification)
                elif channel == NotificationChannel.SMS:
                    success = await self._send_sms(notification)
                elif channel == NotificationChannel.WEBHOOK:
                    success = await self._send_webhook(notification)
                else:
                    success = False
                
                results[channel.value] = success
                
            except Exception as e:
                results[channel.value] = False
                self.failed_notifications.append({
                    "notification": notification,
                    "channel": channel,
                    "error": str(e),
                    "timestamp": time.time()
                })
        
        # Mettre à jour rate limit
        self.last_sent[priority] = time.time()
        
        return {
            "sent": any(results.values()),
            "results": results,
            "notification_id": len(self.notification_history) - 1
        }
    
    async def _send_telegram(self, notification: Notification) -> bool:
        """Envoie via Telegram"""
        if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
            return False
        
        # Simuler l'envoi (remplacer par vraie implémentation)
        print(f"📱 [TELEGRAM] {notification.priority.value.upper()}: {notification.title}")
        print(f"   {notification.message}")
        
        # Vraie implémentation utiliserait:
        # import telegram
        # bot = telegram.Bot(token=self.config.telegram_bot_token)
        # await bot.send_message(chat_id=self.config.telegram_chat_id, text=f"*{notification.title}*\n{notification.message}", parse_mode='Markdown')
        
        return True
    
    async def _send_slack(self, notification: Notification) -> bool:
        """Envoie via Slack"""
        if not self.config.slack_webhook_url:
            return False
        
        print(f"💬 [SLACK] {notification.priority.value.upper()}: {notification.title}")
        
        # Vraie implémentation:
        # import requests
        # payload = {
        #     "text": f"*{notification.title}*",
        #     "attachments": [{
        #         "text": notification.message,
        #         "color": "danger" if notification.priority == NotificationPriority.CRITICAL else "good"
        #     }]
        # }
        # requests.post(self.config.slack_webhook_url, json=payload)
        
        return True
    
    async def _send_email(self, notification: Notification) -> bool:
        """Envoie via Email"""
        if not all([self.config.email_from, self.config.email_to, self.config.email_smtp_host]):
            return False
        
        print(f"📧 [EMAIL] To: {self.config.email_to}")
        print(f"   Subject: {notification.title}")
        
        # Vraie implémentation:
        # import smtplib
        # from email.mime.text import MIMEText
        # msg = MIMEText(notification.message)
        # msg['Subject'] = notification.title
        # msg['From'] = self.config.email_from
        # msg['To'] = self.config.email_to
        # with smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port) as server:
        #     server.starttls()
        #     server.login(self.config.email_from, self.config.email_password)
        #     server.send_message(msg)
        
        return True
    
    async def _send_sms(self, notification: Notification) -> bool:
        """Envoie via SMS"""
        if not self.config.sms_api_key or not self.config.sms_to:
            return False
        
        print(f"📞 [SMS] To: {self.config.sms_to}")
        print(f"   {notification.title}: {notification.message[:100]}")
        
        # Utiliser service comme Twilio
        return True
    
    async def _send_webhook(self, notification: Notification) -> bool:
        """Envoie via Webhook custom"""
        if not self.config.webhook_url:
            return False
        
        print(f"🔗 [WEBHOOK] {notification.title}")
        
        # import requests
        # payload = {
        #     "title": notification.title,
        #     "message": notification.message,
        #     "priority": notification.priority.value,
        #     "timestamp": notification.timestamp,
        #     "metadata": notification.metadata
        # }
        # requests.post(self.config.webhook_url, json=payload)
        
        return True
    
    def _get_default_channels(self, priority: NotificationPriority) -> List[NotificationChannel]:
        """Détermine les canaux par défaut selon la priorité"""
        if priority == NotificationPriority.CRITICAL:
            return [NotificationChannel.TELEGRAM, NotificationChannel.EMAIL, NotificationChannel.SMS]
        elif priority == NotificationPriority.HIGH:
            return [NotificationChannel.TELEGRAM, NotificationChannel.SLACK]
        elif priority == NotificationPriority.MEDIUM:
            return [NotificationChannel.TELEGRAM]
        else:
            return [NotificationChannel.SLACK]
    
    def _can_send(self, priority: NotificationPriority) -> bool:
        """Vérifie le rate limiting"""
        last_time = self.last_sent.get(priority, 0)
        min_interval = self.rate_limits.get(priority, 0)
        
        return (time.time() - last_time) >= min_interval
    
    def get_statistics(self) -> Dict:
        """Statistiques des notifications"""
        by_priority = {}
        by_channel = {}
        
        for notif in self.notification_history:
            priority = notif.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            for channel in notif.channels:
                ch = channel.value
                by_channel[ch] = by_channel.get(ch, 0) + 1
        
        return {
            "total_sent": len(self.notification_history),
            "total_failed": len(self.failed_notifications),
            "by_priority": by_priority,
            "by_channel": by_channel,
            "last_24h": sum(1 for n in self.notification_history if time.time() - n.timestamp < 86400)
        }


# Exemple d'utilisation
async def main():
    config = NotificationConfig(
        telegram_bot_token="YOUR_BOT_TOKEN",
        telegram_chat_id="YOUR_CHAT_ID",
        slack_webhook_url="https://hooks.slack.com/...",
        email_from="bot@example.com",
        email_to="trader@example.com"
    )
    
    manager = NotificationManager(config)
    
    # Notification critique
    await manager.send(
        title="🚨 Stop Loss Triggered",
        message="Position BTCUSDT closed at $49,500 with -2% loss",
        priority=NotificationPriority.CRITICAL,
        metadata={"symbol": "BTCUSDT", "pnl": -500}
    )
    
    # Notification normale
    await manager.send(
        title="✅ Trade Executed",
        message="Bought 0.1 BTC at $50,000",
        priority=NotificationPriority.MEDIUM
    )
    
    print("\n📊 Stats:", manager.get_statistics())


if __name__ == "__main__":
    asyncio.run(main())
