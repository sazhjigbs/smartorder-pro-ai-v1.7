# SmartOrder PRO AI v3.0 - Dashboard React + MUI

## 📋 Vue d'ensemble

Dashboard professionnel React + TypeScript + Material-UI avec architecture moderne et connexion temps réel via WebSocket.

**Stack technique:**
- React 18.2 + TypeScript 5.0
- Material-UI v5 (composants + icons)
- ApexCharts (graphiques PnL/RSI/MACD)
- Framer Motion (animations)
- Zustand (state management)
- Axios (API calls)
- WebSocket natif (real-time updates)
- Vite (build tool ultra-rapide)

## 🎨 Design

- **Theme:** Dark premium avec glassmorphism
- **Colors:** Background #0b0e11, Cards #1e2329, Green #0ecb81, Red #f6465d, Yellow #f0b90b, Blue #3861fb, Purple #9c4bff
- **Responsive:** Mobile (<768px), Tablet (768-1024px), Desktop (>1024px)
- **Animations:** Transitions fluides 0.3-0.5s
- **Performance:** TTI target <2s

## 📦 Installation locale

```bash
cd /opt/smartorder-pro/web/
npm install
```

## 🔧 Configuration

Créer un fichier `.env` à la racine:

```env
VITE_API_URL=http://107.189.22.255:8091/api
VITE_WS_URL=ws://107.189.22.255:8182
```

Pour développement local (avec proxy Vite):
```env
VITE_API_URL=/api
VITE_WS_URL=ws://localhost:8182
```

## 🚀 Commandes

### Développement (hot reload)
```bash
npm run dev
```
Ouvert sur http://localhost:3000

### Build production
```bash
npm run build
```
Génère le dossier `dist/` optimisé

### Preview production
```bash
npm run preview
```

### Lint
```bash
npm run lint
```

## 🏗️ Architecture

```
src/
├── components/
│   ├── Header.tsx              # Mode Selector (Spot/Futures/Hybrid)
│   ├── ExchangeSelector.tsx    # Statut exchanges + toggle
│   ├── Watchlist.tsx            # 10 coins + top gainers
│   ├── StrategiesPanel.tsx      # 14 strategies (6 Spot, 6 Futures, 2 Hybrid)
│   ├── RiskPanel.tsx            # Market Reliability, Drawdown, PnL
│   ├── PositionsTable.tsx       # Tables Spot/Futures + AI recommendations
│   ├── AIFusionStatus.tsx       # 4 AI layers (Learner, Genetic, Reinforcement, Behavior)
│   └── EmergencyStop.tsx        # Bouton d'arrêt d'urgence
├── services/
│   └── api.ts                   # 27 endpoints API (20 existants + 7 nouveaux)
├── hooks/
│   └── useWebSocket.ts          # Hook WebSocket avec reconnexion auto
├── types.ts                     # Interfaces TypeScript
├── theme.ts                     # Theme MUI dark + glassmorphism
├── App.tsx                      # Layout principal Grid responsive
└── main.tsx                     # Entry point React
```

## 🔌 Endpoints API utilisés (27 total)

### Existants (20)
- GET `/api/wallet` - Balance/PnL
- GET `/api/positions` - Positions (query: ?mode=spot|futures)
- GET `/api/exchanges` - Liste exchanges
- POST `/api/exchanges/simple-toggle` - Toggle exchange
- GET `/api/strategies` - 14 stratégies
- POST `/api/strategies/bulk-toggle` - Toggle multiple strategies
- GET `/api/mode` - Mode actuel
- POST `/api/mode` - Changer mode
- GET `/api/modes/status` - Statistiques modes
- POST `/api/modes/auto-select` - Auto-sélection IA
- GET `/api/pnl` - PnL total/daily/weekly
- GET `/api/market-regime` - Régime marché
- GET `/api/risk/status` - Reliability Score, Mode, Drawdown
- POST `/api/risk/mode` - Changer risk mode
- GET `/api/risk/history` - Historique risk changes
- POST `/api/guardian/stop` - Emergency stop
- POST `/api/guardian/resume` - Resume trading
- GET `/api/watchlist` - 10 assets

### Nouveaux (7)
- GET `/api/exchanges/status` - Statut Connected/Offline + latency
- GET `/api/ai/fusion-status` - 4 AI layers status (trust score, patterns, generation, episodes, sentiment)
- GET `/api/positions/ai-decisions` - Recommandations IA par position (action, reason, confidence, urgency)
- GET `/api/signals/realtime` - Signal validator scores (RSI, MACD, EMA, Volume, Regime)
- POST `/api/watchlist/manage` - Add/remove coins (body: {symbol, action: 'add'|'remove'})
- GET `/api/watchlist/gainers` - Top gainers 24h (query: ?limit=5)
- GET `/api/wallet/unified` - Bybit Unified Wallet (Spot + Futures fusionné)

## 🔄 WebSocket (Port 8182)

Le dashboard se connecte automatiquement au WebSocket pour les mises à jour temps réel (refresh ≤3s).

**Format messages:**
```json
{
  "type": "positions_update",
  "data": {...}
}
```

**Reconnexion automatique:** 10 tentatives espacées de 3s

## 🧪 Tests de recette

### Checklist validation (12 sections obligatoires)

- [ ] **Header + Mode Selector:** Affiche mode actuel + toggle Spot/Futures/Hybrid instantané
- [ ] **Exchanges Selector:** 5 exchanges affichés + statut CONNECTED/OFFLINE correct + latency affichée + toggle persistant
- [ ] **Watchlist:** 10 coins affichés + prix live + % 24h + volume + bouton "Top Gainers" fonctionnel + add/remove OK
- [ ] **Strategies Panel:** 14 stratégies visibles (6 Spot, 6 Futures, 2 Hybrid) + ON/OFF toggle + score IA + win_rate affichés
- [ ] **Risk Panel:** Market Reliability Score (68%), Mode BALANCED, Drawdown Day %, Win Rate, PnL Daily/Weekly/Total affichés
- [ ] **Positions Table:** Séparation tabs Spot/Futures + PnL % et USDT corrects + liquidation price (Futures) + AI recommendations inline
- [ ] **AI Fusion Status:** Trust Score 84% + 4 layers (Learner 127 patterns, Genetic Gen 24, Reinforcement 450 episodes, Behavior emotion)
- [ ] **AI Recommendations:** Bande alerte par position avec action (MOVE_TO_BREAKEVEN) + reason + confidence + urgency color-coded
- [ ] **Emergency Stop:** Bouton visible + dialog confirmation + appel API `/api/guardian/stop` fonctionnel
- [ ] **WebSocket:** Indicateur connexion 🟢/🔴 affiché + reconnexion auto testée (couper serveur WS puis relancer)
- [ ] **Responsive:** Layout adaptatif mobile/tablette/desktop (tester Chrome DevTools)
- [ ] **Performance:** TTI < 2s local, aucun blocage render, pas d'erreurs console

### Tests endpoints critiques
```bash
# Sur VPS
curl http://localhost:8091/api/exchanges/status
curl http://localhost:8091/api/ai/fusion-status
curl http://localhost:8091/api/positions/ai-decisions
curl "http://localhost:8091/api/signals/realtime?symbol=BTCUSDT"
curl http://localhost:8091/api/watchlist/gainers
curl http://localhost:8091/api/wallet/unified
```

## 📊 Composants UI détaillés

### 1. Header (sticky)
- Logo + titre "SmartOrder PRO AI v3.0"
- Mode Selector (ButtonGroup 3 modes)
- Chip statut mode actif

### 2. ExchangeSelector
- 5 exchanges (Bybit Spot, Bybit Futures, Binance, OKX, KuCoin)
- Icône CheckCircle/Cancel selon statut
- Latency affichée si connected
- Switch toggle persistant

### 3. Watchlist
- Table 10 assets (Symbol, Price, 24h %, Volume)
- Bouton "Top Gainers" → affiche 5 suggestions
- Bouton Delete par ligne
- Bouton Add sur gainers

### 4. StrategiesPanel (3 sections)
- **SPOT (6):** rsi_macd_bb, volume_surge, swing_break, ema_cross, support_resistance, bollinger_bounce
- **FUTURES (6):** breakout_trend, momentum_pulse, range_bounce, volatility_rider, scalp_master, trend_follower
- **HYBRID (2):** adaptive_hedge, safeswitch
- Chaque carte: nom + switch ON/OFF + score IA + win_rate + last_signal

### 5. RiskPanel (Grid 8 metrics)
- Market Reliability (LinearProgress)
- Mode (Chip BALANCED/AGGRESSIVE/CONSERVATIVE)
- Drawdown Day % (rouge si >5%)
- Win Rate %
- PnL Daily (icon TrendingUp/Down)
- PnL Weekly
- PnL Total
- Trades Today

### 6. PositionsTable (Tabs Spot/Futures)
- Colonnes: Symbol, Side, Entry, Current, PnL %, PnL USDT
- Futures: + Liquidation Price
- AI Recommendation inline (Alert severity selon urgency)

### 7. AIFusionStatus
- Trust Score global (LinearProgress purple)
- 4 cartes layers:
  - Learner: patterns learned, accuracy
  - Genetic: generation, best fitness
  - Reinforcement: episodes, avg reward
  - Behavior: emotion, fear/greed index

### 8. EmergencyStop
- Bouton rouge "EMERGENCY STOP"
- Dialog confirmation 2FA
- POST `/api/guardian/stop`

## 🚀 Déploiement VPS

### 1. Upload sur VPS
```bash
# Depuis local
scp -r dashboard-react/ root@107.189.22.255:/opt/smartorder-pro/web/
```

### 2. Installation
```bash
ssh root@107.189.22.255
cd /opt/smartorder-pro/web/
npm install
```

### 3. Configuration .env
```bash
echo "VITE_API_URL=http://107.189.22.255:8091/api" > .env
echo "VITE_WS_URL=ws://107.189.22.255:8182" >> .env
```

### 4. Build production
```bash
npm run build
```

### 5. Servir avec nginx
Le dossier `dist/` est servi par nginx sur port 8181.

Config nginx (`/etc/nginx/sites-available/smartorder`):
```nginx
server {
    listen 8181;
    root /opt/smartorder-pro/web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8091/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. Restart nginx
```bash
systemctl restart nginx
```

### 7. Accès
http://107.189.22.255:8181

## 🔒 Sécurité

- Aucune clé API exposée côté client
- Toutes les actions passent par backend FastAPI
- JWT auth prévu (localStorage/HTTPOnly cookie)
- CORS configuré sur API

## 📈 Performance

- **Bundle size target:** <500KB gzipped
- **TTI (Time to Interactive):** <2s local, <4s VPS
- **Code splitting:** Vendor/MUI/Charts chunks séparés
- **Lazy loading:** Composants chargés on-demand
- **Memoization:** React.memo sur composants lourds
- **WebSocket:** Throttle updates 3s minimum

## 🐛 Troubleshooting

### "Failed to fetch API"
- Vérifier que smartorder-api tourne: `systemctl status smartorder-api`
- Vérifier VITE_API_URL dans .env
- Tester endpoint: `curl http://localhost:8091/api/strategies`

### "WebSocket connection failed"
- Vérifier smartorder-websocket: `systemctl status smartorder-websocket`
- Vérifier VITE_WS_URL dans .env
- Tester: `wscat -c ws://localhost:8182`

### "npm install erreurs"
- Node version >= 18: `node -v`
- Nettoyer cache: `rm -rf node_modules package-lock.json && npm install`

### "Build errors TypeScript"
- Vérifier imports: tous les types doivent être définis
- `npm run lint` pour voir erreurs détaillées

## 📞 Support

Pour toute question sur le dashboard UI React, vérifier :
1. Logs backend API: `/opt/smartorder-pro/logs/api.log`
2. Logs WebSocket: `/opt/smartorder-pro/logs/websocket.log`
3. Console navigateur (F12) pour erreurs frontend

---

**Version:** 3.0.0  
**Dernière mise à jour:** 2025-11-05  
**Auteur:** SmartOrder PRO AI Team
