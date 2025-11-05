// SmartOrder PRO AI - TypeScript Types
// NULL-SAFE interfaces matching backend API

export type TradingMode = 'spot' | 'futures' | 'hybrid';

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
  last_signal?: string | null;
  last_signal_time?: string | null;
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
  quantity?: number | null;
  size?: number | null;
  pnl_usdt?: number | null;
  pnl_pct?: number | null;
  unrealizedPnl?: number | null;
  mode?: 'spot' | 'futures' | 'paper';
  leverage?: number | null;
  liquidation_price?: number | null;
  stop_loss?: number | null;
  take_profit?: number | null;
  status?: string;
}

export interface Wallet {
  total_equity?: number | null;
  total_wallet_balance?: number | null;
  total_available_balance?: number | null;
  available_balance?: number | null;
  total_unrealized_pnl?: number | null;
  total_realized_pnl?: number | null;
  total_margin_used?: number | null;
  margin_used?: number | null;
  margin_ratio?: number | null;
  pnl_total?: number | null;
  account_type?: string;
}

export interface RiskData {
  reliability_score?: number | null;
  current_mode?: string | null;
  drawdown_day_pct?: number | null;
  max_drawdown_pct?: number | null;
  pnl_day?: number | null;
  total_pnl?: number | null;
  daily_pnl?: number | null;
  weekly_pnl?: number | null;
  trades_today?: number | null;
  win_rate?: number | null;
  last_update?: string;
}

export interface PnLData {
  total?: number | null;
  daily?: number | null;
  weekly?: number | null;
  monthly?: number | null;
  roi_pct?: number | null;
  trades_total?: number | null;
  trades_won?: number | null;
  trades_lost?: number | null;
}

export interface WatchlistAsset {
  symbol: string;
  price?: number | null;
  change_24h?: number | null;
  volume?: number | null;
  market_cap?: number | null;
  last_update?: string;
}

export interface AIFusion {
  fusion_active: boolean;
  trust_score: number;
  last_update?: string;
  learner?: {
    active: boolean;
    patterns_learned: number;
    accuracy: number;
    last_training?: string;
    model_version?: string;
  };
  genetic?: {
    active: boolean;
    generation: number;
    best_fitness: number;
    population_size?: number;
    mutation_rate?: number;
  };
  reinforcement?: {
    active: boolean;
    total_episodes: number;
    avg_reward: number;
    epsilon?: number;
    learning_rate?: number;
  };
  behavior?: {
    active: boolean;
    market_emotion: string;
    fear_greed_index: number;
    confidence: number;
    sentiment: string;
  };
}

export interface AIDecision {
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price?: number;
  current_price?: number;
  pnl_pct?: number;
  pnl_usdt?: number;
  action: 'HOLD' | 'CLOSE' | 'MOVE_TO_BREAKEVEN' | 'TRAILING_STOP' | 'SCALE_OUT';
  reason: string;
  confidence: number;
  urgency: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface Signal {
  symbol: string;
  timeframe: string;
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  indicators?: any;
  regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  volatility: 'LOW' | 'MEDIUM' | 'HIGH';
  ai_confidence: number;
  last_update?: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  source?: string;
}

export interface ModeStatus {
  current_mode?: string | null;
  spot_active?: boolean | null;
  futures_active?: boolean | null;
  hybrid_active?: boolean | null;
  spot?: {
    total: number;
    active: number;
    trades_today: number;
    pnl_today: number;
  };
  futures?: {
    total: number;
    active: number;
    trades_today: number;
    pnl_today: number;
  };
  hybrid?: {
    total: number;
    active: number;
    trades_today: number;
    pnl_today: number;
  };
}

export interface Gainer {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
}
