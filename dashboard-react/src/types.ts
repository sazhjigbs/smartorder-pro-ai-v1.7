// Trading Modes
export type TradingMode = 'spot' | 'futures' | 'hybrid';

// Exchange
export interface Exchange {
  id: string;
  name: string;
  enabled: boolean;
  status?: 'CONNECTED' | 'DISABLED' | 'OFFLINE';
  api_configured?: boolean;
  last_ping?: string;
  latency_ms?: number | null;
}

// Strategy
export interface Strategy {
  id: string;
  name: string;
  type: 'SPOT' | 'FUTURES' | 'HYBRID';
  enabled: boolean;
  score?: number;
  performance?: number;
  trades_today?: number;
  win_rate?: number;
  last_signal?: string;
  last_signal_time?: string;
}

// Position
export interface Position {
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price: number;
  current_price: number;
  quantity: number;
  pnl_usdt: number;
  pnl_pct: number;
  mode: 'spot' | 'futures';
  leverage?: number;
  liquidation_price?: number;
  stop_loss?: number;
  take_profit?: number;
  status?: string;
}

// Wallet
export interface Wallet {
  total_equity: number;
  total_wallet_balance: number;
  total_available_balance: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  total_margin_used?: number;
  margin_ratio?: number;
  account_type?: string;
  currencies?: WalletCurrency[];
}

export interface WalletCurrency {
  coin: string;
  equity: number;
  wallet_balance: number;
  available_balance: number;
  locked: number;
}

// Risk Management
export interface RiskData {
  reliability_score: number;
  current_mode: string;
  drawdown_day_pct: number;
  max_drawdown_pct: number;
  total_pnl: number;
  daily_pnl: number;
  weekly_pnl: number;
  trades_today: number;
  win_rate: number;
  last_update: string;
}

// AI Fusion
export interface AIFusion {
  fusion_active: boolean;
  trust_score: number;
  last_update: string;
  learner: {
    active: boolean;
    patterns_learned: number;
    accuracy: number;
    last_training: string;
    model_version: string;
  };
  genetic: {
    active: boolean;
    generation: number;
    best_fitness: number;
    population_size: number;
    mutation_rate: number;
  };
  reinforcement: {
    active: boolean;
    total_episodes: number;
    avg_reward: number;
    epsilon: number;
    learning_rate: number;
  };
  behavior: {
    active: boolean;
    market_emotion: string;
    fear_greed_index: number;
    confidence: number;
    sentiment: string;
  };
}

// AI Decision
export interface AIDecision {
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price: number;
  current_price: number;
  pnl_pct: number;
  pnl_usdt: number;
  action: 'HOLD' | 'CLOSE' | 'MOVE_TO_BREAKEVEN' | 'TRAILING_STOP' | 'SCALE_OUT';
  reason: string;
  confidence: number;
  urgency: 'LOW' | 'MEDIUM' | 'HIGH';
}

// Signal Validator
export interface Signal {
  symbol: string;
  timeframe: string;
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  indicators: {
    rsi: number;
    rsi_signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    macd: number;
    macd_signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    volume: number;
    volume_ratio: number;
    atr: number;
    ema_20: number;
    ema_50: number;
  };
  regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  volatility: 'LOW' | 'MEDIUM' | 'HIGH';
  ai_confidence: number;
  last_update: string;
}

// Watchlist
export interface WatchlistAsset {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
  market_cap?: number;
  last_update?: string;
}

// PnL Data
export interface PnLData {
  total: number;
  daily: number;
  weekly: number;
  monthly?: number;
  roi_pct?: number;
  trades_total?: number;
  trades_won?: number;
  trades_lost?: number;
}

// Market Regime
export interface MarketRegime {
  regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  ai_confidence: number;
  volatility: 'LOW' | 'MEDIUM' | 'HIGH';
  trend_strength: number;
  last_update: string;
}

// Log Entry
export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  source?: string;
}

// Mode Status
export interface ModeStatus {
  spot: {
    total: number;
    active: number;
    trades_today: number;
    pnl_today: number;
  };
  futures: {
    total: number;
    active: number;
    trades_today: number;
    pnl_today: number;
  };
  hybrid: {
    total: number;
    active: number;
    trades_today: number;
    pnl_today: number;
  };
}

// Gainer
export interface Gainer {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
}
