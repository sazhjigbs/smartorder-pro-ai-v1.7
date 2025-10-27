# 📖 GUIDE D'UTILISATION - SmartOrder PRO
## SAFELOGIC Trading Bot v1.7
### by MAIGA ABOUBACAR

---

## 📋 Table des Matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Démarrage](#démarrage)
5. [Utilisation](#utilisation)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Sécurité](#sécurité)
9. [FAQ](#faq)

---

## 🎯 Introduction

**SmartOrder PRO** est un bot de trading crypto avancé avec intelligence artificielle intégrée.

### Features principales:

- ✅ **Multi-Exchange**: Bybit, Binance (extensible)
- ✅ **AI Multi-Layer**: Fusion AI + Genetic AI + Behavior AI
- ✅ **Modes Trading**: AUTO_SPOT, AUTO_FUTURES, MANUAL, HYBRID
- ✅ **Paper Trading**: Testez sans risque avant de trader réel
- ✅ **Dashboard Web**: Interface moderne sur port 8555
- ✅ **Telegram Bot**: Contrôle et alertes via Telegram
- ✅ **Execution Engine**: Split orders, trailing stop, partial close
- ✅ **Risk Management**: Stop loss, take profit, max drawdown
- ✅ **Sentiment Analysis**: Fear & Greed, BTC dominance, volatilité

---

## 📦 Installation

### Prérequis

- **OS**: Linux (Ubuntu 20.04+), VPS recommandé
- **Python**: 3.9+
- **RAM**: 2GB minimum
- **Stockage**: 10GB minimum

### Étapes d'installation

#### 1. Cloner le repository

```bash
cd /opt
git clone https://github.com/yourusername/smartorder-pro-ai.git smartorder-pro
cd smartorder-pro
```

#### 2. Installer les dépendances

```bash
# Créer un virtualenv (optionnel mais recommandé)
python3 -m venv venv
source venv/bin/activate

# Installer les packages
pip install -r requirements.txt
```

#### 3. Créer le fichier `.env`

```bash
cp .env.example .env
nano .env
```

Contenu du `.env`:

```env
# Bybit API
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_API_SECRET=your_bybit_api_secret_here
BYBIT_RECV_WINDOW=5000

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Database
DATABASE_PATH=data/smartorder.db

# Security
SESSION_SECRET=your_random_secret_here
JWT_SECRET=your_jwt_secret_here

# Logging
LOG_LEVEL=INFO
```

#### 4. Rendre les scripts exécutables

```bash
chmod +x start_bot.sh
chmod +x stop_bot.sh
```

---

## ⚙️ Configuration

### Configuration centralisée

Le bot utilise un fichier de configuration centralisé: `config/bot_config.json`

#### Structure de la config:

```json
{
  "trading": {
    "mode": "manual",           // manual, auto_spot, auto_futures, hybrid
    "paper_trading": true,      // true = simulation, false = réel
    "max_position_size_usd": 100,
    "max_daily_trades": 10,
    "min_confidence_threshold": 0.75
  },
  "risk_management": {
    "stop_loss_percent": 2.5,
    "take_profit_percent": 5.0,
    "max_drawdown_percent": 10
  },
  "strategies": {
    "auto_spot": {
      "enabled": false,
      "coins": ["BTC", "ETH", "SOL"]
    },
    "auto_futures": {
      "enabled": false,
      "leverage": 2
    }
  }
}
```

#### Modifier la config via Python:

```python
from core.config_manager import get_config

config = get_config()

# Lire
paper_trading = config.get("trading.paper_trading")

# Modifier
config.set("trading.mode", "auto_spot")
config.save()
```

### Configuration des Exchanges

#### Bybit:

1. Créer une API Key sur [Bybit](https://www.bybit.com/app/user/api-management)
2. Permissions requises: `Read`, `Trade`
3. IP Whitelist (recommandé): Ajouter l'IP de votre VPS
4. Copier API Key et Secret dans `.env`

#### Binance (optionnel):

Même processus que Bybit, ajouter:

```env
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

---

## 🚀 Démarrage

### Démarrage automatique (recommandé)

```bash
./start_bot.sh
```

Ce script:
- Vérifie les prérequis
- Initialise le bot state
- Démarre le dashboard (port 8555)
- Vérifie les services AI
- Affiche un résumé

### Démarrage manuel

```bash
# Dashboard FastAPI
python3 -m uvicorn web.portal_v5_pro.main_unified:app --host 0.0.0.0 --port 8555 &

# Services AI (si configurés)
sudo systemctl start smartorder-fusion-ai.service
sudo systemctl start smartorder-genetic.service
sudo systemctl start smartorder-behavior.service
```

### Arrêt du bot

```bash
./stop_bot.sh
```

---

## 💻 Utilisation

### Dashboard Web

Accéder au dashboard: `http://votre-ip:8555`

#### Pages disponibles:

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Vue d'ensemble + TradingView |
| Login | `/login` | Authentification JWT |
| Analytics | `/analytics` | Analyses détaillées |
| Trading Control | `/trading` | Contrôles Start/Stop/Pause |
| Mode Selector | `/modes` | Changer le mode de trading |
| Positions | Tab dans `/` | Positions futures |
| Execution | Tab dans `/` | Split orders, trailing stop |

#### Authentification:

Credentials par défaut:
- **Username**: `admin`
- **Password**: `smartorder2025`

⚠️ **Changer le mot de passe après première connexion !**

### Trading Control

#### Modes de trading:

1. **MANUAL**: Contrôle manuel complet
   - Vous placez les ordres manuellement
   - L'IA suggère mais n'exécute pas

2. **AUTO_SPOT**: Trading automatique spot
   - Bot trade automatiquement sur spot
   - Coins configurés dans `config/bot_config.json`

3. **AUTO_FUTURES**: Trading automatique futures
   - Bot trade automatiquement sur futures (perpétuels)
   - Leverage configuré dans config

4. **HYBRID**: IA suggère, vous validez
   - L'IA génère des signaux
   - Vous approuvez/rejetez via dashboard ou Telegram

#### Actions disponibles:

```
START     → Démarre le bot
STOP      → Arrête le bot
PAUSE     → Met en pause (temporaire)
RESUME    → Reprend après pause
EMERGENCY → Arrêt d'urgence + ferme toutes positions
```

### Paper Trading

Le **paper trading** permet de tester le bot sans risque réel.

#### Activer paper trading:

```bash
# Via config
nano config/bot_config.json
# Mettre "paper_trading": true

# Ou via Python
from core.config_manager import get_config
config = get_config()
config.set("trading.paper_trading", True)
config.save()
```

#### Vérifier l'état:

```bash
# Via bot state
python3 -c "from core.bot_state_manager import get_state_manager; print(get_state_manager().get_full_state())"
```

Le wallet virtuel démarre avec **10,000 USDT** par défaut.

### Telegram Bot

#### Commandes disponibles:

```
/start         - Démarre le bot Telegram
/status        - État du bot
/balance       - Solde et positions
/pnl           - PNL du jour
/signals       - Derniers signaux IA
/trade         - Placer un ordre manuel
/stop_all      - Fermer toutes positions
/emergency     - Arrêt d'urgence
/help          - Aide
```

#### Configurer:

1. Créer un bot via [@BotFather](https://t.me/botfather)
2. Obtenir le token
3. Obtenir votre chat_id via [@userinfobot](https://t.me/userinfobot)
4. Ajouter dans `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

---

## 📊 Monitoring

### Logs

Les logs sont dans `logs/`:

```bash
# Dashboard logs
tail -f logs/dashboard.log

# Bot logs
tail -f logs/bot.log

# AI services logs
journalctl -u smartorder-fusion-ai.service -f
```

### Health Check

```bash
# Via API
curl http://localhost:8555/api/ping

# Via dashboard
http://your-ip:8555/api/execution/health
```

### Métriques

Le dashboard affiche en temps réel:
- CPU, RAM, Disk usage
- Nombre de trades
- PNL total
- Positions ouvertes
- Signaux IA récents

### Base de données

Le bot utilise SQLite:

```bash
# Accéder à la DB
sqlite3 data/smartorder.db

# Voir les tables
.tables

# Voir les trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;
```

---

## 🔧 Troubleshooting

### Le dashboard ne démarre pas

**Symptômes**: Erreur au démarrage

**Solutions**:
1. Vérifier que le port 8555 n'est pas utilisé:
   ```bash
   lsof -i :8555
   ```

2. Vérifier les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

3. Vérifier les logs:
   ```bash
   tail -f logs/dashboard.log
   ```

### Erreur "API Key invalid"

**Symptômes**: Erreur lors des requêtes API

**Solutions**:
1. Vérifier que les clés API sont correctes dans `.env`
2. Vérifier les permissions API (Read + Trade)
3. Vérifier l'IP whitelist sur Bybit
4. Tester manuellement:
   ```bash
   python3 -c "from core.bybit_client import system_ping; print(system_ping())"
   ```

### Le bot ne place pas de trades

**Symptômes**: Signaux IA OK mais pas d'exécution

**Solutions**:
1. Vérifier que `paper_trading` est `false` pour trader réel
2. Vérifier que le mode est `auto_spot` ou `auto_futures`
3. Vérifier que le bot est `running`:
   ```bash
   python3 -c "from core.bot_state_manager import get_state_manager; print(get_state_manager().get_status())"
   ```
4. Vérifier les seuils de confiance:
   ```json
   "min_confidence_threshold": 0.75
   ```

### Services AI ne démarrent pas

**Symptômes**: Services systemd inactifs

**Solutions**:
1. Vérifier les fichiers service:
   ```bash
   sudo systemctl status smartorder-fusion-ai.service
   ```

2. Voir les logs:
   ```bash
   journalctl -u smartorder-fusion-ai.service -n 50
   ```

3. Redémarrer:
   ```bash
   sudo systemctl restart smartorder-fusion-ai.service
   ```

### Positions ne s'affichent pas

**Symptômes**: Dashboard affiche "No positions"

**Solutions**:
1. Vérifier que vous avez des positions ouvertes sur l'exchange
2. Vérifier les permissions API (Read)
3. Tester manuellement:
   ```bash
   python3 -c "from core.bybit_client import futures_positions; print(futures_positions())"
   ```

---

## 🔒 Sécurité

### Best Practices

1. **API Keys**:
   - ✅ Utiliser des clés API dédiées au bot
   - ✅ Activer l'IP whitelist
   - ✅ Permissions minimales (Read + Trade uniquement)
   - ❌ Jamais partager les clés
   - ❌ Jamais commit les clés dans Git

2. **Dashboard**:
   - ✅ Changer le mot de passe par défaut
   - ✅ Utiliser HTTPS (reverse proxy Nginx)
   - ✅ Firewall: Limiter l'accès au port 8555
   - ❌ Ne pas exposer publiquement sans auth

3. **VPS**:
   - ✅ SSH avec clé (pas de password)
   - ✅ Firewall configuré (UFW/iptables)
   - ✅ Updates régulières
   - ✅ Fail2ban activé

### Permissions API recommandées

**Bybit**:
- ✅ Read
- ✅ Trade
- ❌ Withdraw (JAMAIS activer)
- ❌ Transfer

### Firewall configuration

```bash
# UFW
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8555/tcp    # Dashboard
sudo ufw enable

# Limiter l'accès au dashboard à votre IP
sudo ufw delete allow 8555/tcp
sudo ufw allow from YOUR_IP to any port 8555
```

### Backup

```bash
# Backup automatique de la DB
cp data/smartorder.db backups/smartorder_$(date +%Y%m%d).db

# Backup config
cp config/bot_config.json backups/bot_config_$(date +%Y%m%d).json

# Backup .env
cp .env backups/.env_$(date +%Y%m%d)
```

---

## ❓ FAQ

### Q: Le bot peut trader automatiquement ?
**R**: Oui, en mode `AUTO_SPOT` ou `AUTO_FUTURES`. Configurer dans `config/bot_config.json`.

### Q: C'est safe de laisser le bot tourner 24/7 ?
**R**: Oui, le bot est conçu pour tourner en continu. Recommandations:
- Commencer avec paper trading
- Utiliser des limites (max_position_size, max_daily_trades)
- Activer stop loss
- Surveiller les logs

### Q: Comment tester sans risque ?
**R**: Activer `paper_trading: true` dans la config. Le bot simulera les trades avec un wallet virtuel.

### Q: Combien ça coûte à utiliser ?
**R**: Le bot est open-source et gratuit. Coûts:
- VPS: ~$5-10/mois (Contabo, Digital Ocean, etc.)
- Frais de trading: Selon l'exchange (0.1% Bybit)

### Q: Quel capital minimum ?
**R**: Dépend de l'exchange. Recommandation:
- Paper trading: $0 (gratuit)
- Trading réel: $100 minimum (pour tester)
- Trading sérieux: $1000+

### Q: Les signaux IA sont fiables ?
**R**: L'IA aide mais n'est pas infaillible. Le bot intègre:
- 3 AI layers (Fusion + Genetic + Behavior)
- Sentiment analysis
- Risk management

⚠️ **Toujours surveiller et ne jamais trader plus que vous pouvez perdre !**

### Q: Comment ajouter un nouvel exchange ?
**R**: Créer un nouveau client dans `core/` similaire à `bybit_client.py`, puis l'intégrer dans `config/bot_config.json`.

### Q: Le bot fonctionne sur Windows ?
**R**: Non recommandé. Le bot est optimisé pour Linux. Utilisez WSL ou un VPS Linux.

---

## 📞 Support

- **GitHub**: [Issues](https://github.com/yourusername/smartorder-pro-ai/issues)
- **Telegram**: @MaigaAboubacar
- **Email**: contact@safelogic.com

---

## 📜 Changelog

### v1.7 (2025-01-27)
- ✅ Dashboard FastAPI unifié (port 8555)
- ✅ Mode Selector (4 modes)
- ✅ Paper Trading Engine
- ✅ Config centralisé
- ✅ Signal Simulator
- ✅ Scripts start/stop automatiques
- ✅ Bot State Manager
- ✅ Positions réelles affichées

### v1.6
- Trading Control API
- Execution Engine
- JWT Auth

### v1.5
- Multi-AI integration
- Sentiment analysis

---

## 📄 Licence

MIT License - Libre d'utilisation

---

**Développé avec ❤️ by MAIGA ABOUBACAR**  
**SAFELOGIC - Smart Trading Solutions**  

⚠️ **Disclaimer**: Le trading crypto comporte des risques. Utilisez ce bot à vos propres risques. Nous ne sommes pas responsables des pertes financières.

---

**Version**: 1.7  
**Dernière mise à jour**: 27/01/2025  
**Statut**: Production Ready ✅
