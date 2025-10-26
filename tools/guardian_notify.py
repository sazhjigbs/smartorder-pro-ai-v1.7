#!/usr/bin/env python3
"""
📱 SAFELOGIC SmartOrder PRO — Guardian Notify
Notifications Telegram instantanées sur événements critiques
"""

import os
import requests
import json
import time
from datetime import datetime

# Configuration Telegram depuis .env
TG_TOKEN = os.getenv("TG_TOKEN", "8280762810:AAHZd13j46iXcwXIENpTeIUmbyJwLTAL260")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "278054920")
TG_ADMIN = os.getenv("TG_ADMIN", "Aboubakr_Maiga")

def send_telegram(message, silent=False):
    """Send notification to Telegram"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ Telegram config missing")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_notification": silent
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Telegram sent: {message[:50]}...")
            return True
        else:
            print(f"❌ Telegram failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Telegram error: {str(e)}")
        return False

def notify_system_start():
    """Notify system startup"""
    message = f"""🚀 *SAFELOGIC SmartOrder PRO*

✅ Système démarré
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 Admin: @{TG_ADMIN}

Modules actifs:
• Portal v5 ✅
• WebSync Bridge ✅  
• Guardian AI ✅
• Auto-Sync GitHub ✅"""

    send_telegram(message)

def notify_crash(service_name, error_details):
    """Notify service crash"""
    message = f"""🚨 *ALERTE CRITIQUE*

💥 Service crashed: `{service_name}`
🕐 {datetime.now().strftime('%H:%M:%S')}

**Erreur:**
```
{error_details[:200]}...
```

🔄 Auto-restart en cours...
👤 @{TG_ADMIN}"""

    send_telegram(message)

def notify_api_error(endpoint, error_code, details):
    """Notify API errors"""
    message = f"""⚠️ *API ERROR*

🌐 Endpoint: `{endpoint}`
🔢 Code: `{error_code}`
🕐 {datetime.now().strftime('%H:%M:%S')}

**Détails:**
```
{details[:150]}...
```"""

    send_telegram(message, silent=True)

def notify_github_sync(status, changes_count=0):
    """Notify GitHub sync events"""
    if status == "success":
        emoji = "✅"
        msg = f"Sync réussi ({changes_count} fichiers)"
    elif status == "error":
        emoji = "❌"
        msg = "Sync failed"
    else:
        emoji = "🔄"
        msg = "Sync en cours"
    
    message = f"""🔁 *GitHub Sync*

{emoji} {msg}
🕐 {datetime.now().strftime('%H:%M:%S')}
🌿 Branch: main"""

    send_telegram(message, silent=True)

def notify_trading_alert(symbol, action, price, pnl=None):
    """Notify trading events"""
    pnl_text = f"\n💰 PnL: {pnl}" if pnl else ""
    
    message = f"""📈 *TRADING ALERT*

🔸 {symbol} {action.upper()}
💵 Prix: ${price}
🕐 {datetime.now().strftime('%H:%M:%S')}{pnl_text}

🤖 ExecutionAI v2.0"""

    send_telegram(message)

def notify_ai_status(phase, confidence, bias):
    """Notify AI status updates"""
    message = f"""🧠 *AI STATUS UPDATE*

📊 Phase: {phase}
🎯 Confiance: {confidence}%
🔮 Biais: {bias}
🕐 {datetime.now().strftime('%H:%M:%S')}

🚀 MTF Fusion AI active"""

    send_telegram(message, silent=True)

def notify_daily_report(stats):
    """Send daily performance report"""
    message = f"""📊 *RAPPORT QUOTIDIEN*

📅 {datetime.now().strftime('%Y-%m-%d')}

**Performance:**
💰 PnL: {stats.get('pnl', 'N/A')}
📈 Trades: {stats.get('trades', 0)}
🎯 Win Rate: {stats.get('win_rate', 'N/A')}%

**Système:**
⚡ Uptime: {stats.get('uptime', 'N/A')}
🔄 Syncs: {stats.get('syncs', 0)}
⚠️ Erreurs: {stats.get('errors', 0)}

🤖 SAFELOGIC SmartOrder PRO v1.8"""

    send_telegram(message)

def test_notifications():
    """Test all notification types"""
    print("🧪 Testing Telegram notifications...")
    
    # Test basic notification
    send_telegram("🧪 Test notification - Guardian active!")
    
    time.sleep(2)
    
    # Test system start
    notify_system_start()
    
    time.sleep(2)
    
    # Test GitHub sync
    notify_github_sync("success", 3)
    
    print("✅ Notification tests completed")

if __name__ == "__main__":
    test_notifications()