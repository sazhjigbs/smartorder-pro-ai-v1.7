#!/usr/bin/env python3
"""
Générateur de Dashboard SmartOrder PRO AI v3.0
Architecture React + TypeScript + MUI robuste avec gestion NULL
"""

import os
import json

BASE_DIR = "/opt/smartorder-pro/web-v3"

files = {
    # === CONFIGURATION ===
    "vite.config.ts": """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8091',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material'],
          charts: ['apexcharts', 'react-apexcharts']
        }
      }
    }
  }
});
""",

    "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
""",

    "tsconfig.node.json": """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
""",

    ".env": """VITE_API_URL=/api
VITE_WS_URL=ws://107.189.22.255:8182
""",

    "index.html": """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SmartOrder PRO AI v3.0</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
""",

    # === TYPES ===
    "src/types.ts": """// NULL-SAFE Types - Toutes les valeurs peuvent être null/undefined
export type TradingMode = 'spot' | 'futures' | 'hybrid';

export interface Exchange {
  id: string;
  name: string;
  enabled: boolean;
  status?: string;
  api_configured?: boolean;
  last_ping?: string;
  latency_ms?: number | null;
}

export interface Strategy {
  id?: string;
  name: string;
  type: string;
  mode: string;
  enabled?: boolean | null;  // PEUT ÊTRE NULL
  active?: boolean | null;
  score?: number | null;
  performance?: number | null;
  trades_today?: number | null;
  win_rate?: number | null;
  last_signal?: string | null;
}

export interface Position {
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price?: number | null;
  current_price?: number | null;
  quantity?: number | null;
  size?: number | null;  // PEUT ÊTRE NULL
  pnl_usdt?: number | null;
  pnl_pct?: number | null;
  unrealizedPnl?: number | null;  // PEUT ÊTRE NULL
  mode?: string;
  leverage?: number | null;
  liquidation_price?: number | null;
}

export interface Wallet {
  total_equity?: number | null;
  total_wallet_balance?: number | null;
  total_available_balance?: number | null;
  available_balance?: number | null;  // PEUT ÊTRE NULL
  total_unrealized_pnl?: number | null;
  total_margin_used?: number | null;
  margin_used?: number | null;  // PEUT ÊTRE NULL
  pnl_total?: number | null;  // PEUT ÊTRE NULL
}

export interface RiskData {
  reliability_score?: number | null;
  current_mode?: string | null;
  drawdown_day_pct?: number | null;  // PEUT ÊTRE NULL
  max_drawdown_pct?: number | null;
  pnl_day?: number | null;  // PEUT ÊTRE NULL
  trades_today?: number | null;
  win_rate?: number | null;
  last_update?: string;
}

export interface PnLData {
  total?: number | null;
  daily?: number | null;
  weekly?: number | null;
}

export interface WatchlistAsset {
  symbol: string;
  price?: number | null;
  change_24h?: number | null;
  volume?: number | null;
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
  action: string;
  reason: string;
  confidence: number;
  urgency: string;
}
""",

    # === UTILS ===
    "src/utils/format.ts": """// Utilitaires de formatting NULL-SAFE

export const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) return '0.00';
  return value.toFixed(decimals);
};

export const formatPercent = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) return '0.00%';
  return `${value.toFixed(decimals)}%`;
};

export const formatCurrency = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) return '$0.00';
  return `$${value.toFixed(decimals)}`;
};

export const safeNumber = (value: number | null | undefined, fallback: number = 0): number => {
  if (value === null || value === undefined || isNaN(value)) return fallback;
  return value;
};
""",

    # === API SERVICE ===
    "src/services/api.ts": """import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

// Interceptor pour gérer les NULL et erreurs
api.interceptors.response.use(
  (response) => {
    // Transformer les réponses pour garantir structures cohérentes
    if (response.config.url?.includes('/positions') && Array.isArray(response.data)) {
      // Si /positions retourne array direct, wrapper dans objet
      response.data = { positions: response.data };
    }
    if (response.config.url?.includes('/watchlist') && response.data.coins) {
      // Renommer coins en assets
      response.data.assets = response.data.coins;
      delete response.data.coins;
    }
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// EXCHANGES
export const getExchangesStatus = () => api.get('/exchanges/status');

// STRATEGIES
export const getStrategies = () => api.get('/strategies');

// POSITIONS
export const getPositions = (mode?: string) => api.get('/positions', { params: mode ? { mode } : {} });

// WALLET
export const getWallet = () => api.get('/wallet/unified');

// RISK
export const getRiskStatus = () => api.get('/risk/status');

// PNL
export const getPnL = () => api.get('/pnl');

// WATCHLIST
export const getWatchlist = () => api.get('/watchlist');

// AI
export const getAIFusionStatus = () => api.get('/ai/fusion-status');
export const getAIDecisions = () => api.get('/positions/ai-decisions');

// MODE
export const getCurrentMode = () => api.get('/mode');
export const setMode = (mode: string) => api.post('/mode', { mode });

// EMERGENCY
export const emergencyStop = () => api.post('/guardian/stop');

export default api;
""",

    # === WEBSOCKET HOOK ===
    "src/hooks/useWebSocket.ts": """import { useEffect, useRef, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://107.189.22.255:8182';

export const useWebSocket = () => {
  const [data, setData] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = () => {
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('[WS] Connected');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setData(message);
        } catch (e) {
          console.error('[WS] Parse error:', e);
        }
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected');
        setConnected(false);
        // Reconnect after 3s
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WS] Connection error:', error);
    }
  };

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return { data, connected };
};
""",

    # === THEME ===
    "src/theme.ts": """import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#0ecb81' },
    secondary: { main: '#f6465d' },
    background: {
      default: '#0b0e11',
      paper: '#1e2329'
    },
    text: {
      primary: '#eaecef',
      secondary: '#b7bdc6'
    },
    success: { main: '#0ecb81' },
    error: { main: '#f6465d' },
    warning: { main: '#fcd535' },
    info: { main: '#3861fb' }
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h6: { fontWeight: 600 },
    body1: { fontSize: '0.95rem' }
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(30, 35, 41, 0.6)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          borderRadius: 12
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', borderRadius: 8 }
      }
    }
  }
});
""",
}

# Créer la structure src/
dirs = [
    "src",
    "src/components",
    "src/services",
    "src/hooks",
    "src/utils"
]

print("#!/bin/bash")
print("# Script de génération Dashboard SmartOrder PRO AI v3.0")
print("")

# Créer les répertoires
for dir_path in dirs:
    print(f"mkdir -p {BASE_DIR}/{dir_path}")

print("")

# Créer tous les fichiers
for file_path, content in files.items():
    full_path = f"{BASE_DIR}/{file_path}"
    # Échapper les caractères spéciaux pour bash
    escaped_content = content.replace("'", "'\\''").replace("$", "\\$").replace("`", "\\`")
    print(f"cat > '{full_path}' << 'FILEOF'")
    print(content)
    print("FILEOF")
    print("")

print("echo '✅ Fichiers de configuration créés'")
print("cd /opt/smartorder-pro/web-v3")
print("npm install")
print("echo '✅ Dépendances installées'")
