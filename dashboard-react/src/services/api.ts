import axios from 'axios';
import type {
  Exchange,
  Strategy,
  Position,
  Wallet,
  RiskData,
  AIFusion,
  AIDecision,
  Signal,
  WatchlistAsset,
  PnLData,
  MarketRegime,
  ModeStatus,
  Gainer,
  TradingMode,
} from '../types';

const API_BASE = (import.meta as any).env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor pour JWT (si implémenté)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ========== EXCHANGES ==========
export const getExchanges = () => api.get<{ exchanges: Exchange[] }>('/exchanges');
export const getExchangesStatus = () => api.get<{ exchanges: Exchange[]; total: number; connected: number }>('/exchanges/status');
export const toggleExchange = (exchangeId: string, enabled: boolean) =>
  api.post('/exchanges/simple-toggle', { exchange_id: exchangeId, enabled });

// ========== STRATEGIES ==========
export const getStrategies = () => api.get<{ strategies: Strategy[] }>('/strategies');
export const bulkToggleStrategies = (strategyIds: string[], enabled: boolean) =>
  api.post('/strategies/bulk-toggle', { strategy_ids: strategyIds, enabled });

// ========== MODES ==========
export const getCurrentMode = () => api.get<{ mode: TradingMode }>('/mode');
export const setMode = (mode: TradingMode) => api.post('/mode', { mode });
export const getModeStatus = () => api.get<ModeStatus>('/modes/status');
export const autoSelectModes = (threshold: number) => api.post('/modes/auto-select', { threshold });

// ========== POSITIONS ==========
export const getPositions = (mode?: 'spot' | 'futures') => {
  const params = mode ? { mode } : {};
  return api.get<{ positions: Position[] }>('/positions', { params });
};

// ========== WALLET ==========
export const getWallet = () => api.get<Wallet>('/wallet');
export const getUnifiedWallet = () => api.get<Wallet>('/wallet/unified');

// ========== PNL ==========
export const getPnL = () => api.get<PnLData>('/pnl');

// ========== RISK MANAGEMENT ==========
export const getRiskStatus = () => api.get<RiskData>('/risk/status');
export const getRiskHistory = () => api.get<any>('/risk/history');
export const setRiskMode = (mode: string) => api.post('/risk/mode', { mode });

// ========== AI FUSION ==========
export const getAIFusionStatus = () => api.get<AIFusion>('/ai/fusion-status');

// ========== AI DECISIONS ==========
export const getAIDecisions = () => api.get<{ decisions: AIDecision[]; count: number; market_reliability: number; last_update: string }>('/positions/ai-decisions');

// ========== SIGNALS ==========
export const getRealtimeSignal = (symbol: string, timeframe: string = '15m') =>
  api.get<Signal>('/signals/realtime', { params: { symbol, timeframe } });

// ========== WATCHLIST ==========
export const getWatchlist = () => api.get<{ assets: WatchlistAsset[] }>('/watchlist');
export const manageWatchlist = (symbol: string, action: 'add' | 'remove') =>
  api.post('/watchlist/manage', { symbol, action });
export const getGainers = (limit: number = 5) => api.get<{ gainers: Gainer[]; count: number }>('/watchlist/gainers', { params: { limit } });

// ========== MARKET REGIME ==========
export const getMarketRegime = () => api.get<MarketRegime>('/market-regime');

// ========== GUARDIAN ==========
export const emergencyStop = () => api.post('/guardian/stop');
export const emergencyResume = () => api.post('/guardian/resume');

export default api;
