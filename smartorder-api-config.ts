// SmartOrder PRO AI - API Configuration
// Connexion au backend FastAPI (port 8091)

export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8091/api',
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://107.189.22.255:8182',
  ENDPOINTS: {
    // Strategies
    STRATEGIES: '/strategies',
    STRATEGIES_TOGGLE: '/strategies/bulk-toggle',
    
    // Exchanges
    EXCHANGES: '/exchanges',
    EXCHANGES_STATUS: '/exchanges/status',
    EXCHANGES_TOGGLE: '/exchanges/simple-toggle',
    
    // Modes
    MODE_CURRENT: '/mode',
    MODE_STATUS: '/modes/status',
    MODE_AUTO_SELECT: '/modes/auto-select',
    
    // Positions
    POSITIONS: '/positions',
    POSITIONS_AI_DECISIONS: '/positions/ai-decisions',
    
    // Wallet
    WALLET: '/wallet',
    WALLET_UNIFIED: '/wallet/unified',
    
    // Risk
    RISK_STATUS: '/risk/status',
    RISK_HISTORY: '/risk/history',
    RISK_MODE: '/risk/mode',
    
    // PnL
    PNL: '/pnl',
    
    // Watchlist
    WATCHLIST: '/watchlist',
    WATCHLIST_MANAGE: '/watchlist/manage',
    WATCHLIST_GAINERS: '/watchlist/gainers',
    
    // AI
    AI_FUSION: '/ai/fusion-status',
    
    // Signals
    SIGNALS_REALTIME: '/signals/realtime',
    
    // Market
    MARKET_REGIME: '/market-regime',
    
    // Guardian
    GUARDIAN_STOP: '/guardian/stop',
    GUARDIAN_RESUME: '/guardian/resume',
  }
};

// NULL-SAFE utilities
export const safe = (value: any, fallback: any = 0) => {
  return (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) 
    ? fallback 
    : value;
};

export const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
  return safe(value, 0).toFixed(decimals);
};

export const formatCurrency = (value: number | null | undefined): string => {
  return `$${formatNumber(value, 2)}`;
};

export const formatPercent = (value: number | null | undefined): string => {
  return `${formatNumber(value, 2)}%`;
};
