# 🤖 Déploiement Bot Telegram + Trading Auto

## 📋 Prérequis

### 1. Token Telegram Bot
```bash
# Parler à @BotFather sur Telegram
# Commandes:
/newbot
# Suivre instructions, récupérer token
```

### 2. Votre User ID Telegram
```bash
# Parler à @userinfobot sur Telegram
# Il vous donnera votre user ID (ex: 123456789)
```

### 3. Ajouter au .env sur VPS
```bash
nano /opt/smartorder-pro/.env

# Ajouter ces lignes:
TELEGRAM_BOT_TOKEN=votre_token_ici
TELEGRAM_ALLOWED_USERS=votre_user_id_ici
```

---

## 🚀 Installation sur VPS

### 1. Pull le code
```bash
cd /opt/smartorder-pro
git pull origin main
```

### 2. Installer dépendances Python
```bash
source venv/bin/activate
pip install -r requirements_telegram.txt
```

### 3. Créer dossier telegram
```bash
mkdir -p /opt/smartorder-pro/telegram
```

### 4. Copier services systemd
```bash
# Bot Telegram
cp deploy/smartorder-telegram.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smartorder-telegram
systemctl start smartorder-telegram

# Trading Auto
cp deploy/smartorder-trading.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smartorder-trading
systemctl start smartorder-trading
```

### 5. Vérifier status
```bash
# Bot Telegram
systemctl status smartorder-telegram

# Trading Auto
systemctl status smartorder-trading
```

---

## 📱 Test Bot Telegram

### 1. Chercher votre bot sur Telegram
Cherchez le nom donné à @BotFather

### 2. Commandes disponibles
```
/start          - Menu principal
/position       - Voir positions ouvertes
/balance        - Voir balances
/pnl            - Résumé PNL
/status         - État du bot

/trade BUY BTCUSDT 0.001    - Trade manuel
/split BTCUSDT 0.003 67000  - Split order
/trailing BTCUSDT LONG 67000 2.0  - Trailing stop

/start_trading  - Activer trading auto
/stop_trading   - Désactiver trading auto
```

### 3. Test rapide
```
/start
/status
/position
```

---

## ⚙️ Configuration Trading Auto

### Fichier: `core/auto_trading_engine.py`

Paramètres à ajuster selon votre stratégie:

```python
# Risk Management
self.max_positions = 3          # Max 3 positions simultanées
self.max_daily_loss = 50.0      # Stop si -50 USDT/jour
self.max_position_size = 100.0  # Taille max par position
self.min_confidence = 0.65      # Confiance min (65%)
self.min_trust_score = 70.0     # Trust score min (70)

# Trading
self.leverage = 2               # Levier x2
self.stop_loss_pct = 2.0        # Stop-loss 2%
self.take_profit_pct = 5.0      # Take-profit 5%
self.min_trade_interval = 300   # Min 5 min entre trades
```

---

## 📊 Monitoring

### Logs en temps réel
```bash
# Bot Telegram
tail -f /opt/smartorder-pro/logs/telegram_bot.log

# Trading Auto
tail -f /opt/smartorder-pro/logs/auto_trading.log
```

### Vérifier ressources
```bash
# CPU/RAM des services
systemctl status smartorder-telegram
systemctl status smartorder-trading

# Ou via htop
htop
```

---

## 🔄 Redémarrage

```bash
# Bot Telegram
systemctl restart smartorder-telegram

# Trading Auto
systemctl restart smartorder-trading

# Les deux
systemctl restart smartorder-telegram smartorder-trading
```

---

## 🛑 Arrêt

```bash
# Bot Telegram
systemctl stop smartorder-telegram

# Trading Auto
systemctl stop smartorder-trading
```

---

## 🧪 Tests Manuels

### Test Bot Telegram (sans service)
```bash
cd /opt/smartorder-pro
source venv/bin/activate
export TELEGRAM_BOT_TOKEN="votre_token"
export TELEGRAM_ALLOWED_USERS="votre_id"
python3 telegram/telegram_bot.py
```

### Test Trading Auto (sans service)
```bash
cd /opt/smartorder-pro
source venv/bin/activate
python3 core/auto_trading_engine.py
```

---

## ⚠️ Sécurité

### 1. Whitelist User ID
Seuls les user IDs dans `TELEGRAM_ALLOWED_USERS` peuvent utiliser le bot.

Format:
```bash
# Un seul user
TELEGRAM_ALLOWED_USERS=123456789

# Plusieurs users (séparés par virgule)
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

### 2. Mode Testnet d'abord !
Testez avec Bybit Testnet avant production:
```bash
# Dans .env
BYBIT_TESTNET=true
```

### 3. Petites quantités
Commencez avec des petites positions (10-20 USDT) pour tester.

---

## 🐛 Dépannage

### Bot Telegram ne répond pas
```bash
# 1. Vérifier service
systemctl status smartorder-telegram

# 2. Vérifier logs
tail -50 /opt/smartorder-pro/logs/telegram_bot.log

# 3. Vérifier token
echo $TELEGRAM_BOT_TOKEN

# 4. Test manuel
cd /opt/smartorder-pro && source venv/bin/activate
python3 telegram/telegram_bot.py
```

### Trading Auto ne trade pas
```bash
# 1. Vérifier si activé
# Sur Telegram: /status

# 2. Vérifier signaux AI
cat /opt/smartorder-pro/db/market_memory.json

# 3. Vérifier logs
tail -50 /opt/smartorder-pro/logs/auto_trading.log

# 4. Vérifier limites risque
# Check daily_pnl et trades_today dans logs
```

### Erreur "Module not found"
```bash
cd /opt/smartorder-pro
source venv/bin/activate
pip install -r requirements_telegram.txt
systemctl restart smartorder-telegram smartorder-trading
```

---

## 📈 Activation Trading Auto

### Via Telegram
```
/start_trading
```

### Via Dashboard
Aller sur http://107.189.22.255:8555 → Tab "Execution"

### Manuellement
```bash
# Dans le code auto_trading_engine.py, ligne 26:
self.enabled = True
```

---

## 🎯 Workflow Complet

```
1. Setup .env avec tokens
2. Installer services
3. Démarrer Bot Telegram
4. Test commandes Telegram
5. Activer Trading Auto via /start_trading
6. Monitorer logs
7. Profiter ! 🚀
```

---

## 📞 Support

En cas de problème:
1. Check logs
2. Vérifier .env
3. Test manuel
4. Restart services

---

**Version**: 6.15  
**Date**: 2025-10-26  
**Status**: Production Ready ✅
