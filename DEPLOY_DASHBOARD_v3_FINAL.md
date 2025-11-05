# 🚀 SmartOrder PRO AI v2.4 - Dashboard v3.0 FINAL + Risk Manager AI

## 📦 Déploiement Complet

### Étape 1 : Upload des Fichiers au VPS

```bash
# Connexion au VPS
ssh root@107.189.22.255

# Copier le dashboard
scp dashboard_v3_final_integrated.html root@107.189.22.255:/opt/smartorder-pro/web/dashboard.html

# Copier le module Risk Manager
scp api/risk_manager.py root@107.189.22.255:/opt/smartorder-pro/api/risk_manager.py
```

### Étape 2 : Ajouter les Endpoints Risk Manager dans main.py

Ajouter ces imports en haut de `/opt/smartorder-pro/api/main.py` :

```python
from risk_manager import risk_manager
```

Ajouter ces endpoints avant `if __name__ == "__main__":` :

```python
# =====================
# RISK MANAGEMENT ENDPOINTS
# =====================

@app.get("/api/risk/status")
async def get_risk_status():
    """Get current risk management status"""
    try:
        return risk_manager.get_current_status()
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/risk/mode")
async def set_risk_mode(payload: dict):
    """Set risk mode (manual or auto)"""
    try:
        mode = payload.get("mode")
        auto = payload.get("auto")
        return risk_manager.set_mode(mode, auto)
    except Exception as e:
        return {"error": str(e)}, 500

@app.get("/api/risk/history")
async def get_risk_history(limit: int = 50):
    """Get risk management history"""
    try:
        return {"history": risk_manager.get_history(limit)}
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/guardian/stop")
async def emergency_stop():
    """Activate emergency stop"""
    try:
        result = risk_manager.activate_emergency_stop()
        risk_manager.add_to_history("EMERGENCY_STOP", result)
        return result
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/guardian/resume")
async def emergency_resume():
    """Deactivate emergency stop"""
    try:
        result = risk_manager.deactivate_emergency_stop()
        risk_manager.add_to_history("EMERGENCY_RESUME", result)
        return result
    except Exception as e:
        return {"error": str(e)}, 500
```

### Étape 3 : Redémarrer les Services

```bash
# Redémarrer l'API
systemctl restart smartorder-api

# Vérifier le statut
systemctl status smartorder-api

# Vérifier les logs
journalctl -u smartorder-api -n 50 --no-pager
```

### Étape 4 : Tests des Endpoints

```bash
# Test Risk Status
curl http://localhost:8091/api/risk/status | jq

# Test Risk Mode Change
curl -X POST http://localhost:8091/api/risk/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "AGGRESSIVE", "auto": false}' | jq

# Test Emergency Stop
curl -X POST http://localhost:8091/api/guardian/stop | jq

# Test Risk History
curl http://localhost:8091/api/risk/history?limit=10 | jq
```

### Étape 5 : Accès Dashboard

Ouvrir dans le navigateur :
```
https://107.189.22.255/dashboard
```

## ✅ Vérifications Post-Déploiement

### 1. Dashboard UI
- [ ] Page se charge sans erreur 404
- [ ] Header affiche "SmartOrder PRO AI v2.4"
- [ ] 4 métriques en haut (Balance, PnL, Positions, Win Rate)
- [ ] Panel Risk Management AI visible avec badge de mode
- [ ] Signal Validator Layer avec 5 barres animées
- [ ] Exchange Selector avec 5 boutons
- [ ] 3 sections stratégies (Spot/Futures/Hybrid)
- [ ] 2 tables positions (Spot/Futures)
- [ ] Logs en bas avec couleurs

### 2. WebSocket
- [ ] Status dot vert (Online) dans header
- [ ] Pas d'erreur dans console F12
- [ ] Connection à ws://107.189.22.255:8182 réussie

### 3. API Endpoints (13 total)
```bash
curl http://localhost:8091/api/wallet
curl http://localhost:8091/api/positions
curl http://localhost:8091/api/exchanges
curl http://localhost:8091/api/strategies
curl http://localhost:8091/api/pnl
curl http://localhost:8091/api/market-regime
curl http://localhost:8091/api/risk/status
curl http://localhost:8091/api/mode
curl http://localhost:8091/api/watchlist
```

### 4. Toggles Fonctionnels
- [ ] Cliquer sur "Bybit Spot" → devient vert (active)
- [ ] Cliquer à nouveau → devient gris (inactive)
- [ ] Persiste après refresh page
- [ ] Log visible dans section logs

### 5. Risk Manager
- [ ] Market Reliability Score affiche un %
- [ ] Badge de mode correspond au score :
  - >80% : Mode Aggressif (vert)
  - 60-80% : Mode Équilibré (bleu)
  - 40-60% : Mode Préventif (jaune)
  - <40% : Mode Défensif (rouge)
- [ ] Barre de progression colorée
- [ ] Bouton AUTO fonctionnel
- [ ] Emergency Stop demande confirmation

### 6. Signal Validator
- [ ] Barres affichent des valeurs dynamiques
- [ ] Couleurs changent selon valeur (vert/jaune/rouge)
- [ ] Bouton refresh recharge les données
- [ ] Animation smooth lors du changement

### 7. Positions
- [ ] Table Spot séparée de Futures
- [ ] Compteur correct (X Spot / Y Futures)
- [ ] Colonnes : Symbol, Side, Entry, Value, PnL%
- [ ] Couleur Side : vert (BUY), rouge (SELL)
- [ ] Message "No positions" si vide

### 8. Responsive Mobile
- [ ] Ouvrir sur mobile/tablette
- [ ] Grilles passent en 1 colonne
- [ ] Header stats se cachent
- [ ] Scrolling fluide
- [ ] Boutons tactiles fonctionnels

## 🔧 Dépannage

### Dashboard ne charge pas
```bash
# Vérifier nginx
systemctl status nginx
nginx -t

# Vérifier fichier existe
ls -la /opt/smartorder-pro/web/dashboard.html
```

### API renvoie 500
```bash
# Vérifier logs
journalctl -u smartorder-api -f

# Tester Python syntax
cd /opt/smartorder-pro/api
python3 -c "import risk_manager; print('OK')"
```

### WebSocket ne connecte pas
```bash
# Vérifier service
systemctl status smartorder-websocket

# Vérifier port
netstat -tulpn | grep 8182

# Vérifier firewall
ufw status | grep 8182
```

### Toggles ne persistent pas
```bash
# Vérifier permissions fichiers
ls -la /opt/smartorder-pro/config/
chmod 644 /opt/smartorder-pro/config/*.json
```

## 📊 Structure des Fichiers

```
/opt/smartorder-pro/
├── api/
│   ├── main.py (API FastAPI)
│   ├── risk_manager.py (NEW - Risk Management AI)
│   └── websocket_server.py
├── web/
│   └── dashboard.html (NEW - Dashboard v3.0 FINAL)
├── config/
│   ├── strategies.json (14 stratégies)
│   ├── exchanges_state.json
│   ├── strategies_state.json
│   ├── positions.json
│   ├── paper_wallet.json
│   ├── pnl_tracker.json
│   ├── risk.json (NEW - auto-créé)
│   └── last_signals.json
└── logs/
```

## 🎯 Endpoints Complets

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/wallet` | GET | Balance + PnL total |
| `/api/positions` | GET | Positions ouvertes |
| `/api/positions?mode=spot` | GET | Positions Spot uniquement |
| `/api/positions?mode=futures` | GET | Positions Futures uniquement |
| `/api/exchanges` | GET | Liste exchanges |
| `/api/exchanges/simple-toggle` | POST | Toggle exchange ON/OFF |
| `/api/strategies` | GET | Liste 14 stratégies |
| `/api/strategies/simple-toggle` | POST | Toggle stratégie ON/OFF |
| `/api/pnl` | GET | PnL total/daily/weekly |
| `/api/market-regime` | GET | AI confidence, RSI, MACD, regime |
| `/api/mode` | GET | Mode trading (PAPER/LIVE) |
| `/api/watchlist` | GET | Watchlist assets |
| `/api/risk/status` | GET | ⭐ Risk Manager status complet |
| `/api/risk/mode` | POST | ⭐ Changer mode risk (AGGRESSIVE/BALANCED/etc) |
| `/api/risk/history` | GET | ⭐ Historique changements risk |
| `/api/guardian/stop` | POST | ⭐ Emergency Stop |
| `/api/guardian/resume` | POST | ⭐ Reprendre trading |

## 🚨 Seuils Risk Manager

| Reliability Score | Mode | Max Leverage | Max Positions | Stop Loss | Take Profit |
|-------------------|------|--------------|---------------|-----------|-------------|
| > 80% | AGGRESSIVE | 3x | 10 | 2.5% | 5.0% |
| 60-80% | BALANCED | 2x | 6 | 2.0% | 3.5% |
| 40-60% | PREVENTIVE | 1.5x | 3 | 1.0% | 2.0% |
| 20-40% | DEFENSIVE | 1x | 2 | 0.8% | 1.5% |
| < 20% | SAFE_MODE | 0x | 0 | 0.5% | 1.0% |

## 📱 Formule Market Reliability Score

```
Reliability = (AI_Confidence × 40%) + 
              (Volatility_Score × 20%) + 
              (Regime_Stability × 20%) + 
              (PnL_Consistency × 20%)
```

**Sources de données** :
- AI Confidence : `/config/last_signals.json` → ai_confidence
- Volatility : `/config/last_signals.json` → volatility (LOW=0.9, MEDIUM=0.7, HIGH=0.4)
- Regime : `/config/last_signals.json` → regime (TRENDING=0.85, RANGING=0.80, NEUTRAL=0.70)
- PnL : `/config/pnl_tracker.json` → total_pnl (>100=$0.9, >50=0.8, >0=0.7, <0=décroissant)

## ✨ Fonctionnalités Clés Dashboard v3.0

### Design
- ✅ Style Binance/TradingView professionnel
- ✅ Dark mode (#0b0e11 background)
- ✅ Glassmorphism cards
- ✅ Animations smooth (0.5s transitions)
- ✅ Responsive PC + Mobile (< 1024px = 1 colonne)
- ✅ Font awesome icons
- ✅ Custom scrollbar (6px, dark)

### Interactivité
- ✅ Auto-refresh toutes les 30s
- ✅ WebSocket real-time updates
- ✅ Toggle buttons avec feedback visuel
- ✅ Logs colorés par niveau (info/success/warning/error)
- ✅ Confirmations modales (emergency stop)
- ✅ Status dots animés (pulse)

### Data
- ✅ 100% données réelles API (zero placeholder)
- ✅ Calculs dynamiques (win rate, drawdown, reliability)
- ✅ Séparation Spot/Futures
- ✅ Formatage currency USD
- ✅ Timestamps localisés

## 🎨 Palette Couleurs

```css
--bg-primary: #0b0e11    /* Background principal */
--bg-secondary: #161a1e  /* Cards hover, secondary */
--bg-card: #1e2329       /* Cards background */
--border-color: #2b3139  /* Bordures */
--text-primary: #eaecef  /* Texte principal */
--text-secondary: #848e9c /* Texte secondaire */
--green: #0ecb81         /* Gains, success, buy */
--red: #f6465d           /* Pertes, danger, sell */
--yellow: #f0b90b        /* Warning, branding */
--blue: #3861fb          /* Info, actions */
--purple: #9c4bff        /* Risk panel accent */
```

## 📈 Prochaines Étapes (Phase 7-8)

- [ ] Implémenter AI auto-selection stratégies (score ≥70%)
- [ ] Ajouter filtres regime dans stratégies
- [ ] Créer endpoint `/api/logs/tail` pour logs streaming
- [ ] Améliorer WebSocket broadcasts (positions, wallet, signals)
- [ ] Ajouter graphiques PnL (Chart.js ou ApexCharts)
- [ ] Implémenter Watchlist dynamique avec % variation
- [ ] Créer page Settings pour config bot
- [ ] Ajouter notifications push (Telegram/Discord)
- [ ] Mode LIVE avec confirmations sécurité
- [ ] Backtesting UI intégré

## 🔐 Sécurité

- ⚠️ Dashboard actuellement en HTTP (107.189.22.255)
- ⚠️ Pas d'authentification requise (interne uniquement)
- ⚠️ WebSocket non chiffré (ws://)
- ✅ API interne (localhost:8091 non exposé)
- ✅ Nginx reverse proxy configuré

**Recommandations** :
- Ajouter authentification JWT
- Migrer vers HTTPS (Let's Encrypt)
- WebSocket sécurisé (wss://)
- Rate limiting API
- CORS headers stricts

---

**Dashboard v3.0 FINAL créé le** : 2025-01-XX  
**Auteur** : SmartOrder PRO AI Team  
**Version** : 2.4 (Phase 6.5/8)  
**Status** : ✅ Production Ready (85% → 95% complet)
