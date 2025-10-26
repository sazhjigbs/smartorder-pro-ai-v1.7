#!/usr/bin/env python3
"""
🚨 SAFELOGIC SmartOrder PRO — Advanced Alert Manager
Price alerts, P&L thresholds, position monitoring with Telegram/Email notifications
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Telegram import (optional)
try:
    import telegram
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

class AlertType(str, Enum):
    PRICE = "price"
    PNL = "pnl"
    POSITION = "position"
    DRAWDOWN = "drawdown"
    VOLUME = "volume"
    CUSTOM = "custom"

class AlertCondition(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    CHANGE_PERCENT = "change_percent"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"

class Alert:
    """Alert model"""
    
    def __init__(
        self,
        id: str,
        user: str,
        alert_type: AlertType,
        condition: AlertCondition,
        threshold: float,
        symbol: Optional[str] = None,
        message: str = "",
        telegram_notify: bool = True,
        email_notify: bool = False,
        expires_at: Optional[datetime] = None
    ):
        self.id = id
        self.user = user
        self.alert_type = alert_type
        self.condition = condition
        self.threshold = threshold
        self.symbol = symbol
        self.message = message
        self.telegram_notify = telegram_notify
        self.email_notify = email_notify
        self.status = AlertStatus.ACTIVE
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.triggered_at = None
        self.trigger_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user": self.user,
            "alert_type": self.alert_type,
            "condition": self.condition,
            "threshold": self.threshold,
            "symbol": self.symbol,
            "message": self.message,
            "telegram_notify": self.telegram_notify,
            "email_notify": self.email_notify,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "trigger_count": self.trigger_count
        }

class AlertManager:
    """Manages all alerts and notifications"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alerts_file = "alerts.json"
        self.telegram_bot = None
        self.load_alerts()
        self.init_telegram()
    
    def init_telegram(self):
        """Initialize Telegram bot if available"""
        if TELEGRAM_AVAILABLE:
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if token:
                try:
                    self.telegram_bot = telegram.Bot(token=token)
                    print("✅ Telegram bot initialized")
                except Exception as e:
                    print(f"⚠️ Telegram init failed: {e}")
    
    def load_alerts(self):
        """Load alerts from file"""
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                    for alert_data in data:
                        alert = Alert(**alert_data)
                        self.alerts[alert.id] = alert
        except Exception as e:
            print(f"Error loading alerts: {e}")
    
    def save_alerts(self):
        """Save alerts to file"""
        try:
            data = [alert.to_dict() for alert in self.alerts.values()]
            with open(self.alerts_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving alerts: {e}")
    
    def create_alert(
        self,
        user: str,
        alert_type: AlertType,
        condition: AlertCondition,
        threshold: float,
        **kwargs
    ) -> Alert:
        """Create a new alert"""
        alert_id = f"alert_{datetime.now().timestamp()}"
        alert = Alert(
            id=alert_id,
            user=user,
            alert_type=alert_type,
            condition=condition,
            threshold=threshold,
            **kwargs
        )
        
        self.alerts[alert_id] = alert
        self.save_alerts()
        
        return alert
    
    def get_alerts(self, user: Optional[str] = None, status: Optional[AlertStatus] = None) -> List[Alert]:
        """Get alerts with optional filters"""
        alerts = list(self.alerts.values())
        
        if user:
            alerts = [a for a in alerts if a.user == user]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return alerts
    
    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self.save_alerts()
            return True
        return False
    
    def update_alert_status(self, alert_id: str, status: AlertStatus):
        """Update alert status"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = status
            self.save_alerts()
    
    async def check_price_alert(self, alert: Alert, current_price: float) -> bool:
        """Check if price alert should trigger"""
        if alert.condition == AlertCondition.ABOVE:
            return current_price > alert.threshold
        elif alert.condition == AlertCondition.BELOW:
            return current_price < alert.threshold
        elif alert.condition == AlertCondition.EQUALS:
            # Within 0.1% of threshold
            return abs(current_price - alert.threshold) / alert.threshold < 0.001
        return False
    
    async def check_pnl_alert(self, alert: Alert, current_pnl: float) -> bool:
        """Check if P&L alert should trigger"""
        if alert.condition == AlertCondition.ABOVE:
            return current_pnl > alert.threshold
        elif alert.condition == AlertCondition.BELOW:
            return current_pnl < alert.threshold
        return False
    
    async def send_telegram_notification(self, chat_id: str, message: str):
        """Send Telegram notification"""
        if not self.telegram_bot:
            return False
        
        try:
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    def send_email_notification(self, to_email: str, subject: str, message: str):
        """Send email notification"""
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        
        if not all([smtp_user, smtp_pass]):
            print("⚠️ Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False
    
    async def trigger_alert(self, alert: Alert, current_value: float):
        """Trigger an alert and send notifications"""
        alert.triggered_at = datetime.now()
        alert.trigger_count += 1
        alert.status = AlertStatus.TRIGGERED
        
        # Build notification message
        message = f"""
🚨 <b>Alert Triggered!</b>

<b>Type:</b> {alert.alert_type}
<b>Symbol:</b> {alert.symbol or 'N/A'}
<b>Condition:</b> {alert.condition}
<b>Threshold:</b> {alert.threshold}
<b>Current Value:</b> {current_value}

<b>Message:</b> {alert.message or 'No message'}

<i>Time:</i> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send Telegram notification
        if alert.telegram_notify:
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if chat_id:
                await self.send_telegram_notification(chat_id, message)
        
        # Send Email notification
        if alert.email_notify:
            user_email = os.getenv("USER_EMAIL")
            if user_email:
                self.send_email_notification(
                    user_email,
                    f"SmartOrder Alert: {alert.alert_type}",
                    message.replace('<b>', '<strong>').replace('</b>', '</strong>')
                )
        
        self.save_alerts()
    
    async def check_all_alerts(self, market_data: Dict):
        """Check all active alerts against current market data"""
        for alert in self.get_alerts(status=AlertStatus.ACTIVE):
            # Check expiration
            if alert.expires_at and datetime.now() > alert.expires_at:
                alert.status = AlertStatus.EXPIRED
                continue
            
            triggered = False
            current_value = None
            
            # Check different alert types
            if alert.alert_type == AlertType.PRICE:
                if alert.symbol in market_data.get('prices', {}):
                    current_price = market_data['prices'][alert.symbol]
                    if await self.check_price_alert(alert, current_price):
                        triggered = True
                        current_value = current_price
            
            elif alert.alert_type == AlertType.PNL:
                current_pnl = market_data.get('pnl', 0)
                if await self.check_pnl_alert(alert, current_pnl):
                    triggered = True
                    current_value = current_pnl
            
            elif alert.alert_type == AlertType.POSITION:
                # Check position size
                if alert.symbol in market_data.get('positions', {}):
                    position = market_data['positions'][alert.symbol]
                    current_size = position.get('size', 0)
                    if await self.check_pnl_alert(alert, current_size):
                        triggered = True
                        current_value = current_size
            
            if triggered:
                await self.trigger_alert(alert, current_value)
        
        self.save_alerts()

# Global instance
alert_manager = AlertManager()

# Predefined alert templates
ALERT_TEMPLATES = {
    "btc_50k": {
        "name": "BTC reaches $50,000",
        "alert_type": AlertType.PRICE,
        "condition": AlertCondition.ABOVE,
        "threshold": 50000,
        "symbol": "BTCUSDT"
    },
    "daily_profit_1000": {
        "name": "Daily profit exceeds $1,000",
        "alert_type": AlertType.PNL,
        "condition": AlertCondition.ABOVE,
        "threshold": 1000
    },
    "daily_loss_500": {
        "name": "Daily loss exceeds -$500",
        "alert_type": AlertType.PNL,
        "condition": AlertCondition.BELOW,
        "threshold": -500
    },
    "drawdown_10": {
        "name": "Drawdown exceeds 10%",
        "alert_type": AlertType.DRAWDOWN,
        "condition": AlertCondition.BELOW,
        "threshold": -10
    }
}
