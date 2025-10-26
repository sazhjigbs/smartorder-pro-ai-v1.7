# 🚀 SAFELOGIC SmartOrder PRO v6.0 - Guide d'Utilisation

## 📋 Table des Matières
1. [Accès au Dashboard](#accès-au-dashboard)
2. [Fonctionnalités](#fonctionnalités)
3. [Guide des Onglets](#guide-des-onglets)
4. [API Reference](#api-reference)
5. [Monitoring](#monitoring)
6. [Dépannage](#dépannage)

---

## 🌐 Accès au Dashboard

### URL
```
http://107.189.22.255:8555
```

### Authentification
- **Username**: `admin`
- **Password**: `SmartOrder2025!`

> ⚠️ **Important**: Changez le mot de passe en production dans `web/portal_v5_pro/auth.py`

---

## ✨ Fonctionnalités

### 📊 Dashboard Principal
- **TradingView** : Graphique temps réel BTCUSDT
- **Balances Spot** : Soldes disponibles sur Bybit
- **Système** : CPU, RAM, Uptime en temps réel

### 💼 Positions
- Vue complète positions futures Bybit
- PNL non réalisé en temps réel
- Actions rapides (Close position)

### ⚡ Execution Engine

#### Split Order
Divise un gros ordre en plusieurs petits ordres progressifs.

**Paramètres:**
- **Symbol**: BTCUSDT, ETHUSDT, etc.
- **Side**: BUY / SELL
- **Total Quantity**: Quantité totale à diviser
- **Price**: Prix limite
- **Splits**: Nombre de divisions (2-10)

**Exemple:**
```
Symbol: BTCUSDT
Side: BUY
Quantity: 0.009 BTC
Price: 67000
Splits: 3

→ Créera 3 ordres de 0.003 BTC chacun
```

#### Trailing Stop
Stop-loss dynamique qui suit le prix automatiquement.

**Paramètres:**
- **Symbol**: BTCUSDT, etc.
- **Side**: LONG / SHORT
- **Entry Price**: Prix d'entrée position
- **Trail %**: Pourcentage de trailing (ex: 2%)

**Comment ça marche:**
- **LONG**: Le stop monte avec le prix, mais ne descend jamais
- **SHORT**: Le stop descend avec le prix, mais ne monte jamais
- Déclenché si le prix recule de X% depuis le plus haut/bas

**Exemple LONG:**
```
Entry: 67000
Trail: 2%
Current: 68000

→ Stop automatique à: 66640 (68000 - 2%)
Si prix monte à 69000 → Stop monte à 67620
Si prix redescend à 67620 → TRIGGERED!
```

#### Partial Close
Ferme partiellement une position (25%, 50%, 75%, 100%).

### 📈 PNL Live
- WebSocket Bybit V5 temps réel
- Résumé global des positions
- PNL total et moyen
- Win/Loss ratio

### 🎯 Signals
- Historique des signaux de trading
- Trust Score par signal
- Win rate et PNL moyen
- Statistiques globales

---

## 🎯 Guide des Onglets

### 1️⃣ Dashboard
**Utilisation:**
- Visualiser marché en temps réel
- Vérifier balances spot
- Monitorer santé système

**Rafraîchissement:** Automatique toutes les 5 secondes

### 2️⃣ Positions
**Utilisation:**
- Vue d'ensemble positions ouvertes
- Suivi PNL en temps réel
- Fermeture rapide si nécessaire

**Actions:**
- 🔴 **Close**: Ferme position immédiatement (à venir)

### 3️⃣ Execution
**Utilisation:**
1. **Créer Split Order**:
   - Remplir formulaire gauche
   - Cliquer "Create Split Order"
   - Ordres créés et prêts à exécuter

2. **Setup Trailing Stop**:
   - Remplir formulaire droite
   - Cliquer "Setup Trailing Stop"
   - Monitoring automatique démarre

3. **Gérer Trailing Stops**:
   - Liste des stops actifs en bas
   - Voir prix actuel et stop price
   - Annuler si nécessaire

### 4️⃣ PNL Live
**Utilisation:**
- Voir résumé temps réel
- Positions gagnantes vs perdantes
- PNL total cumulé

**Données:**
- Total Positions
- PNL Total USDT
- PNL Moyen %
- Win/Loss count

### 5️⃣ Signals
**Utilisation:**
- Analyser performance des signaux
- Trust score par stratégie
- Historique complet

**Statistiques:**
- Total signaux
- Wins / Losses
- Win Rate %
- Average PNL %
- Total PNL USDT

---

## 🔌 API Reference

### System APIs

#### Health Check
```bash
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "6.0",
  "execution_engine": true,
  "pnl_api": true
}
```

#### System Status
```bash
GET /api/system_status
```
**Response:**
```json
{
  "cpu": 15.2,
  "ram": 42.8,
  "disk": 35.1,
  "uptime": "02:15:30"
}
```

### Execution APIs

#### Create Split Order
```bash
POST /api/execution/split-order
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "total_quantity": 0.003,
  "price": 67000,
  "num_splits": 3,
  "delay_seconds": 2
}
```

#### Setup Trailing Stop
```bash
POST /api/execution/trailing-stop/setup
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "side": "LONG",
  "entry_price": 67000,
  "trail_percent": 2.0,
  "current_price": 67500
}
```

#### Get All Trailing Stops
```bash
GET /api/execution/trailing-stops
```

#### Cancel Trailing Stop
```bash
DELETE /api/execution/trailing-stop/BTCUSDT
```

### PNL APIs

#### PNL Summary
```bash
GET /api/pnl/summary
```

#### PNL by Symbol
```bash
GET /api/pnl/live/BTCUSDT
```

### Signal APIs

#### Signal Stats
```bash
GET /api/signal/stats
```

#### Signal History
```bash
GET /api/signal/history?limit=10
```

#### Trust Score
```bash
GET /api/signal/trust/BTCUSDT?timeframe=15m&last_n=50
```

---

## 🔍 Monitoring

### Script de Monitoring
```bash
cd /opt/smartorder-pro
chmod +x monitor_system.sh
./monitor_system.sh
```

**Vérifie:**
- ✅ Status services systemd
- ✅ Ports en écoute
- ✅ Ressources système (CPU, RAM, Disk)
- ✅ Health APIs

### Cron Job (Monitoring Automatique)
```bash
# Éditer crontab
crontab -e

# Ajouter ligne (check toutes les 5 minutes)
*/5 * * * * /opt/smartorder-pro/monitor_system.sh >> /opt/smartorder-pro/logs/monitor_cron.log 2>&1
```

### Logs
```bash
# Logs du service
journalctl -u smartorder-portal-v5 -f

# Logs monitoring
tail -f /opt/smartorder-pro/logs/monitor.log

# Logs alertes
tail -f /opt/smartorder-pro/logs/alerts.log
```

---

## 🔧 Dépannage

### Dashboard ne charge pas

**1. Vérifier service**
```bash
systemctl status smartorder-portal-v5
```

**2. Redémarrer si nécessaire**
```bash
systemctl restart smartorder-portal-v5
```

**3. Vérifier logs**
```bash
journalctl -u smartorder-portal-v5 -n 50
```

### Authentification échoue

**Vérifier credentials dans:**
```bash
nano /opt/smartorder-pro/web/portal_v5_pro/auth.py
```

### APIs ne répondent pas

**Test manuel:**
```bash
curl http://localhost:8555/health
curl http://localhost:8555/api/execution/health
curl http://localhost:8555/api/pnl/summary
```

### Positions n'apparaissent pas

**Vérifier clés API Bybit:**
```bash
cat /opt/smartorder-pro/.env
```

**Tester connexion:**
```bash
cd /opt/smartorder-pro
source venv/bin/activate
python3 -c "from core.bybit_client import futures_positions; print(futures_positions())"
```

### Haute utilisation RAM/CPU

**Vérifier processus:**
```bash
top -bn1 | head -20
ps aux | grep python | grep -v grep
```

**Optimiser si nécessaire:**
```bash
# Réduire workers uvicorn
nano /etc/systemd/system/smartorder-portal-v5.service
# Ajouter --workers 1 si nécessaire
```

---

## 📞 Support

### Commandes Utiles

**Redémarrage complet:**
```bash
systemctl restart smartorder-portal-v5
```

**Mise à jour code:**
```bash
cd /opt/smartorder-pro
git pull origin main
systemctl restart smartorder-portal-v5
```

**Check santé système:**
```bash
./monitor_system.sh
```

**Backup base de données:**
```bash
cp data/signals_memory.db data/signals_memory_backup_$(date +%Y%m%d).db
```

---

## 🎯 Prochaines Étapes

1. **Personnaliser authentification** (auth.py)
2. **Configurer alertes** (email/Telegram)
3. **Optimiser stratégies** selon trust scores
4. **Monitorer performance** régulièrement
5. **Backup données** périodiquement

---

**Version**: 6.0  
**Dernière mise à jour**: 2025-10-26  
**Status**: Production Ready ✅
