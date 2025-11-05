# 🚀 PLAN D'INTÉGRATION SMARTORDER PRO AI v3.0
## Template: Next-shadcn-dashboard-starter

**Date**: 2025-11-05  
**Template**: https://github.com/Kiranism/next-shadcn-dashboard-starter  
**Location VPS**: `/opt/smartorder-pro/dashboard-nextjs/`

---

## ✅ ÉTAPES COMPLÉTÉES

1. ✅ **Clone template** → `/opt/smartorder-pro/dashboard-nextjs/`
2. ✅ **Installation dépendances** → 1031 packages (33s)
3. ✅ **Analyse structure** → Next.js 15 + App Router + shadcn/ui

---

## 📋 STRUCTURE TEMPLATE ACTUELLE

```
dashboard-nextjs/
├── src/
│   ├── app/
│   │   ├── dashboard/          # Pages dashboard existantes
│   │   │   ├── overview/       # Page overview (à remplacer)
│   │   │   ├── kanban/         # Page kanban (à supprimer)
│   │   │   ├── product/        # Page products (à supprimer)
│   │   │   └── profile/        # Page profile (à supprimer)
│   │   ├── auth/               # Authentication Clerk (à remplacer par JWT)
│   │   └── layout.tsx
│   ├── components/
│   │   ├── layout/             # Header, Sidebar, etc.
│   │   ├── forms/              # Form components
│   │   └── ui/                 # shadcn/ui components
│   ├── hooks/                  # Custom hooks
│   └── lib/                    # Utilities
├── public/
└── package.json
```

---

## 🎯 MODULES SMARTORDER À CRÉER

### **1. Pages Dashboard (/app/dashboard/)**

**Créer ces nouvelles pages** :

```
/app/dashboard/
├── page.tsx                    # Overview principal (remplacer existant)
├── strategies/
│   └── page.tsx                # 14 AI Strategies + ON/OFF + Scores
├── positions/
│   └── page.tsx                # Positions Spot/Futures + AI Recommendations
├── watchlist/
│   └── page.tsx                # Watchlist 10+ coins + Add/Remove + Gainers
├── risk/
│   └── page.tsx                # Risk Management Panel (Reliability, Drawdown, etc.)
├── exchanges/
│   └── page.tsx                # Exchange Selector + Status + Toggle
└── settings/
    └── page.tsx                # Configuration + Emergency Stop
```

---

### **2. Composants SmartOrder (/components/smartorder/)**

**Créer ces composants** :

```typescript
// Mode Selector Component
/components/smartorder/ModeSelector.tsx
- Boutons: Spot / Futures / Hybrid
- API: POST /api/mode

// Strategies Panel Component
/components/smartorder/StrategiesPanel.tsx
- Liste 14 stratégies
- Toggle ON/OFF par stratégie
- Affichage scores IA
- API: GET /api/strategies, POST /api/strategies/bulk-toggle

// Exchange Selector Component
/components/smartorder/ExchangeSelector.tsx
- Liste 5 exchanges (Bybit, Binance, OKX, KuCoin, etc.)
- Status: Connected/Offline
- Toggle enable/disable
- Latency indicator
- API: GET /api/exchanges/status, POST /api/exchanges/simple-toggle

// Risk Panel Component
/components/smartorder/RiskPanel.tsx
- Market Reliability (progress bar)
- Current Mode (BALANCED/AGGRESSIVE/CONSERVATIVE)
- Drawdown Day %
- Win Rate %
- API: GET /api/risk/status

// Wallet Unified Component
/components/smartorder/WalletUnified.tsx
- Total Equity
- Available Balance
- Margin Used
- PnL Total
- API: GET /api/wallet/unified

// Watchlist Component
/components/smartorder/Watchlist.tsx
- Liste 10+ coins avec prix + change 24h
- Boutons Add/Remove
- Top Gainers scanner
- API: GET /api/watchlist, POST /api/watchlist/manage, GET /api/watchlist/gainers

// Positions Table Component
/components/smartorder/PositionsTable.tsx
- Tabs: Spot / Futures
- Colonnes: Symbol, Side, Entry, Current, PnL, AI Recommendation
- Actions: Hold/Close/Trailing/Breakeven
- API: GET /api/positions, GET /api/positions/ai-decisions

// AI Fusion Status Component
/components/smartorder/AIFusionStatus.tsx
- Trust Score gauge
- 4 AI Layers: Learner, Genetic, Reinforcement, Behavior
- Metrics par layer
- API: GET /api/ai/fusion-status

// Emergency Stop Button Component
/components/smartorder/EmergencyStop.tsx
- Gros bouton rouge
- Confirmation dialog
- API: POST /api/guardian/stop

// WebSocket Indicator Component
/components/smartorder/WebSocketIndicator.tsx
- Point vert/rouge: Connected/Disconnected
- Reconnexion auto
- WebSocket: ws://107.189.22.255:8182
```

---

### **3. Hooks Custom (/hooks/)**

```typescript
// useSmartOrderAPI.ts
- Wrapper pour tous les appels API SmartOrder
- Gestion erreurs et loading states
- NULL-SAFE par défaut

// useWebSocket.ts
- Connexion WebSocket port 8182
- Reconnexion automatique
- Event handlers: positions, wallet, heartbeat

// useStrategies.ts
- Fetch /api/strategies
- Toggle strategies
- Real-time updates

// usePositions.ts
- Fetch /api/positions
- Filter Spot/Futures
- AI decisions integration

// useRisk.ts
- Fetch /api/risk/status
- Real-time risk metrics
- History tracking
```

---

### **4. Types TypeScript (/types/smartorder.ts)**

```typescript
export interface Strategy {
  id?: string;
  name: string;
  type: 'SPOT' | 'FUTURES' | 'HYBRID';
  mode: string;
  enabled?: boolean | null;
  active?: boolean | null;
  score?: number | null;
  performance?: number | null;
  trades_today?: number | null;
  win_rate?: number | null;
}

export interface Exchange {
  id: string;
  name: string;
  enabled: boolean;
  status?: 'CONNECTED' | 'DISABLED' | 'OFFLINE';
  api_configured?: boolean;
  last_ping?: string;
  latency_ms?: number | null;
}

export interface Position {
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price?: number | null;
  current_price?: number | null;
  size?: number | null;
  pnl_usdt?: number | null;
  pnl_pct?: number | null;
  mode?: 'spot' | 'futures';
  leverage?: number | null;
}

export interface RiskData {
  reliability_score?: number | null;
  current_mode?: string | null;
  drawdown_day_pct?: number | null;
  win_rate?: number | null;
  trades_today?: number | null;
}

export interface Wallet {
  total_equity?: number | null;
  available_balance?: number | null;
  margin_used?: number | null;
  pnl_total?: number | null;
}

export interface AIFusion {
  fusion_active: boolean;
  trust_score: number;
  learner?: any;
  genetic?: any;
  reinforcement?: any;
  behavior?: any;
}

export interface AIDecision {
  symbol: string;
  side: string;
  entry_price?: number;
  current_price?: number;
  pnl_pct?: number;
  pnl_usdt?: number;
  action: 'HOLD' | 'CLOSE' | 'MOVE_TO_BREAKEVEN' | 'TRAILING_STOP';
  reason: string;
  confidence: number;
  urgency: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface WatchlistAsset {
  symbol: string;
  price?: number | null;
  change_24h?: number | null;
  volume?: number | null;
}
```

---

## ⚙️ CONFIGURATION REQUISE

### **1. Variables d'environnement (.env.local)**

```bash
# API Backend
NEXT_PUBLIC_API_URL=http://107.189.22.255:8091/api
NEXT_PUBLIC_WS_URL=ws://107.189.22.255:8182

# Disable Clerk Auth (remplacer par JWT simple)
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...  # À SUPPRIMER

# App Info
NEXT_PUBLIC_APP_NAME=SmartOrder PRO AI v3.0
NEXT_PUBLIC_APP_AUTHOR=MAIGA ABOUBAKAR - SAFELOGIC Engineering
```

---

### **2. Proxy API (next.config.ts)**

```typescript
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8091/api/:path*',
      },
    ];
  },
};
```

---

### **3. Theme Dark Premium (globals.css)**

Ajouter le style glassmorphism :

```css
.glassmorphism {
  background: rgba(30, 35, 41, 0.6);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

:root {
  --smartorder-green: #0ecb81;
  --smartorder-red: #f6465d;
  --smartorder-yellow: #fcd535;
  --smartorder-blue: #3861fb;
  --smartorder-bg: #0b0e11;
  --smartorder-card: #1e2329;
}
```

---

## 🔧 MODIFICATIONS TEMPLATE EXISTANT

### **À SUPPRIMER** :

```
❌ src/app/dashboard/kanban/        # Non utilisé
❌ src/app/dashboard/product/       # Non utilisé
❌ src/app/dashboard/profile/       # Non utilisé
❌ src/app/auth/                    # Remplacer par JWT simple
❌ @clerk/nextjs dependency          # Supprimer Clerk
```

---

### **À MODIFIER** :

```typescript
// src/app/dashboard/layout.tsx
// Remplacer sidebar items par:
const sidebarItems = [
  { title: 'Overview', url: '/dashboard', icon: LayoutDashboard },
  { title: 'Strategies', url: '/dashboard/strategies', icon: Brain },
  { title: 'Positions', url: '/dashboard/positions', icon: TrendingUp },
  { title: 'Watchlist', url: '/dashboard/watchlist', icon: Star },
  { title: 'Risk Management', url: '/dashboard/risk', icon: Shield },
  { title: 'Exchanges', url: '/dashboard/exchanges', icon: Network },
  { title: 'Settings', url: '/dashboard/settings', icon: Settings },
];
```

---

## 📦 DÉPENDANCES SUPPLÉMENTAIRES

```bash
npm install axios                    # API calls
npm install recharts                 # Charts avancés
npm install @tanstack/react-query    # Data fetching
npm install zustand                  # State management
```

---

## 🚀 COMMANDES DÉVELOPPEMENT

```bash
# Développement local
cd /opt/smartorder-pro/dashboard-nextjs
npm run dev                          # Port 3000

# Build production
npm run build

# Démarrer production
npm run start                        # Port 3000

# Ou utiliser PM2
pm2 start "npm run start" --name smartorder-dashboard
```

---

## 🌐 DÉPLOIEMENT PRODUCTION

### **Option A: Nginx Reverse Proxy (Recommandé)**

**1. Build Next.js**
```bash
cd /opt/smartorder-pro/dashboard-nextjs
npm run build
npm run start
```

**2. Configurer Nginx**
```nginx
# /etc/nginx/sites-available/smartorder-nextjs
server {
    listen 443 ssl;
    server_name 107.189.22.255;

    ssl_certificate /etc/letsencrypt/live/107.189.22.255/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/107.189.22.255/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8091/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**3. Activer et recharger**
```bash
ln -s /etc/nginx/sites-available/smartorder-nextjs /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

### **Option B: Export Static (Alternative)**

Si tu préfères du static HTML :

```typescript
// next.config.ts
const nextConfig = {
  output: 'export',  // Static export
  images: {
    unoptimized: true,
  },
};
```

```bash
npm run build
# Build généré dans: /opt/smartorder-pro/dashboard-nextjs/out/
# Copier dans nginx: cp -r out/* /opt/smartorder-pro/web/dist/
```

---

## ✅ CHECKLIST VALIDATION

### **Avant déploiement** :

- [ ] Toutes les 14 stratégies affichées
- [ ] Mode Selector fonctionnel (Spot/Futures/Hybrid)
- [ ] Watchlist avec 10+ coins
- [ ] Exchanges status précis (Connected/Offline)
- [ ] Risk Panel avec données réelles (68% reliability)
- [ ] Positions Spot/Futures séparées avec AI Recommendations
- [ ] WebSocket connecté (point vert) avec mise à jour <3s
- [ ] Emergency Stop fonctionnel avec confirmation
- [ ] Design glassmorphism dark premium
- [ ] Responsive mobile/tablet/desktop
- [ ] Zéro erreur console F12
- [ ] Performance TTI <2s

---

## 📊 PRIORITÉS D'IMPLÉMENTATION

### **Phase 1 (Critique - 1 jour)**
1. Configurer .env.local avec API_URL et WS_URL
2. Supprimer Clerk Auth (remplacer par JWT simple ou temporairement désactiver)
3. Créer page /dashboard/page.tsx (Overview)
4. Créer composant ModeSelector
5. Créer composant RiskPanel
6. Créer composant WalletUnified
7. Tester connexion API backend

### **Phase 2 (Essentiel - 2 jours)**
8. Créer page /dashboard/strategies/page.tsx
9. Créer composant StrategiesPanel (14 stratégies)
10. Créer page /dashboard/positions/page.tsx
11. Créer composant PositionsTable (Spot/Futures tabs + AI Reco)
12. Créer composant WebSocketIndicator
13. Intégrer WebSocket temps réel

### **Phase 3 (Important - 1 jour)**
14. Créer page /dashboard/watchlist/page.tsx
15. Créer composant Watchlist (Add/Remove + Gainers)
16. Créer page /dashboard/exchanges/page.tsx
17. Créer composant ExchangeSelector
18. Créer composant AIFusionStatus

### **Phase 4 (Finitions - 1 jour)**
19. Créer composant EmergencyStop
20. Ajouter glassmorphism styling partout
21. Tests responsive mobile/tablet
22. Build production + déploiement nginx
23. Validation complète des 12 critères d'acceptation

---

## 📝 NOTES IMPORTANTES

1. **NULL-SAFE obligatoire** : Utiliser les fonctions `safe()`, `formatNumber()`, `formatCurrency()`, `formatPercent()` partout
2. **WebSocket reconnexion auto** : Implémenter retry logic avec exponential backoff
3. **Error boundaries** : Wrapper chaque page dans ErrorBoundary React
4. **Loading states** : Utiliser Skeleton de shadcn/ui pendant chargement API
5. **TypeScript strict** : Maintenir `strict: true` dans tsconfig.json
6. **Performance** : Code splitting automatique avec Next.js App Router
7. **Signature** : Ajouter "by MAIGA ABOUBAKAR - SAFELOGIC Engineering" en footer

---

## 🎯 RÉSULTAT ATTENDU

Un dashboard **Next.js 15 + TypeScript + shadcn/ui** professionnel qui :
- ✅ Affiche les **vraies données** du backend FastAPI (port 8091)
- ✅ Met à jour en **temps réel** via WebSocket (port 8182)
- ✅ Gère tous les **NULL** correctement (zéro crash)
- ✅ Respecte le **design glassmorphism dark premium**
- ✅ Fonctionne sur **mobile/tablet/desktop**
- ✅ Charge en **<2s** (TTI optimisé)
- ✅ Contient les **12 sections obligatoires** du cahier des charges
- ✅ Est **maintenable** et **évolutif** pour le futur mobile React Native

---

**Template installé**: ✅  
**Prêt pour développement**: ✅  
**Temps estimé implémentation complète**: 5 jours  
**Temps estimé MVP fonctionnel**: 2 jours

---

**Prochaine action**: Créer les composants SmartOrder dans `/opt/smartorder-pro/dashboard-nextjs/src/components/smartorder/`
