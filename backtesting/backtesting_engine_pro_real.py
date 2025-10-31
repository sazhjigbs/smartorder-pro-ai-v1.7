"""
Backtesting Engine PRO - Version RÉELLE
Backtest avec données historiques CCXT + Walk-Forward + Monte Carlo
"""
import time
import numpy as np
import pandas as pd
import ccxt
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("backtest_real")


@dataclass
class BacktestConfig:
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    initial_balance: float = 10000
    days_history: int = 90
    fee_rate: float = 0.001  # 0.1%
    exchange_name: str = "bybit"


class BacktestingEngineReal:
    """Backtesting professionnel avec données CCXT réelles"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.exchange = self._init_exchange()
        self.historical_data: Optional[pd.DataFrame] = None
        
        LOG.info(f"✅ Backtesting Engine REAL initialisé")
        LOG.info(f"   Symbol: {self.config.symbol}")
        LOG.info(f"   Timeframe: {self.config.timeframe}")
        LOG.info(f"   History: {self.config.days_history} jours")
    
    def _init_exchange(self) -> ccxt.Exchange:
        """Initialise exchange CCXT"""
        try:
            if self.config.exchange_name == "bybit":
                exchange = ccxt.bybit({'enableRateLimit': True})
            elif self.config.exchange_name == "binance":
                exchange = ccxt.binance({'enableRateLimit': True})
            else:
                exchange = ccxt.bybit({'enableRateLimit': True})
            
            exchange.load_markets()
            LOG.info(f"✅ Connecté à {self.config.exchange_name}")
            return exchange
        except Exception as e:
            LOG.error(f"❌ Erreur connexion: {e}")
            raise
    
    def fetch_historical_data(self) -> pd.DataFrame:
        """Récupère données historiques RÉELLES depuis CCXT"""
        LOG.info(f"📥 Téléchargement données historiques...")
        
        try:
            # Calcule timestamp de départ
            days = self.config.days_history
            since = self.exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
            
            all_ohlcv = []
            current_since = since
            
            while current_since < self.exchange.milliseconds():
                try:
                    # Récupère batch de 1000 bougies
                    ohlcv = self.exchange.fetch_ohlcv(
                        self.config.symbol,
                        self.config.timeframe,
                        since=current_since,
                        limit=1000
                    )
                    
                    if not ohlcv:
                        break
                    
                    all_ohlcv.extend(ohlcv)
                    current_since = ohlcv[-1][0] + 1
                    
                    LOG.info(f"   Récupéré: {len(all_ohlcv)} bougies")
                    
                    # Rate limiting
                    time.sleep(self.exchange.rateLimit / 1000)
                
                except Exception as e:
                    LOG.warning(f"⚠️ Erreur batch: {e}, retry...")
                    time.sleep(2)
                    continue
            
            # Convertir en DataFrame
            df = pd.DataFrame(
                all_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Ajouter colonne date
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Supprimer doublons
            df = df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)
            
            LOG.info(f"✅ {len(df)} bougies téléchargées")
            LOG.info(f"   Période: {df['date'].min()} → {df['date'].max()}")
            
            self.historical_data = df
            return df
        
        except Exception as e:
            LOG.error(f"❌ Erreur fetch data: {e}")
            raise
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute indicateurs techniques avec bibliothèque 'ta'"""
        try:
            from ta.trend import SMAIndicator, EMAIndicator, MACD
            from ta.momentum import RSIIndicator
            from ta.volatility import BollingerBands, AverageTrueRange
            
            # SMA & EMA
            df['sma_20'] = SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema_20'] = EMAIndicator(df['close'], window=20).ema_indicator()
            df['ema_50'] = EMAIndicator(df['close'], window=50).ema_indicator()
            
            # RSI
            rsi = RSIIndicator(df['close'], window=14)
            df['rsi'] = rsi.rsi()
            
            # MACD
            macd = MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_lower'] = bb.bollinger_lband()
            
            # ATR (volatilité)
            atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14)
            df['atr'] = atr.average_true_range()
            
            LOG.info(f"✅ Indicateurs calculés")
            return df
        
        except Exception as e:
            LOG.error(f"❌ Erreur calcul indicateurs: {e}")
            return df
    
    def run_backtest(self, strategy: Callable, use_indicators=True) -> Dict:
        """
        Exécute backtest simple
        
        Args:
            strategy: Fonction qui prend une row DataFrame et retourne 'buy', 'sell' ou 'hold'
            use_indicators: Ajouter indicateurs techniques
        """
        LOG.info(f"🚀 Démarrage backtest...")
        
        # 1. Récupère données si pas déjà fait
        if self.historical_data is None:
            df = self.fetch_historical_data()
        else:
            df = self.historical_data.copy()
        
        # 2. Ajoute indicateurs
        if use_indicators:
            df = self.add_indicators(df)
        
        # 3. Simule trading
        balance = self.config.initial_balance
        position = None
        trades = []
        equity_curve = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Skip si données manquantes (début indicateurs)
            if pd.isna(row.get('rsi', 0)):
                continue
            
            # Appel stratégie
            signal = strategy(row)
            
            # Exécute signal
            if signal == 'buy' and position is None and balance > 0:
                # Achète
                qty = balance / row['close']
                position = {
                    'entry_price': row['close'],
                    'entry_date': row['date'],
                    'quantity': qty,
                    'entry_index': i
                }
                balance = 0
                
                trades.append({
                    'type': 'buy',
                    'price': row['close'],
                    'date': row['date'],
                    'index': i
                })
            
            elif signal == 'sell' and position is not None:
                # Vend
                exit_price = row['close']
                qty = position['quantity']
                
                # Calcule PnL
                pnl_gross = (exit_price - position['entry_price']) * qty
                fees = (position['entry_price'] * qty + exit_price * qty) * self.config.fee_rate
                pnl_net = pnl_gross - fees
                
                balance = exit_price * qty - fees
                
                trades.append({
                    'type': 'sell',
                    'price': exit_price,
                    'date': row['date'],
                    'index': i,
                    'pnl': pnl_net,
                    'pnl_pct': (pnl_net / (position['entry_price'] * qty)) * 100,
                    'hold_days': (row['date'] - position['entry_date']).days
                })
                
                position = None
            
            # Enregistre equity
            current_equity = balance
            if position:
                current_equity = position['quantity'] * row['close']
            
            equity_curve.append({
                'date': row['date'],
                'equity': current_equity
            })
        
        # 4. Clôture position finale si ouverte
        if position:
            last_price = df.iloc[-1]['close']
            pnl_gross = (last_price - position['entry_price']) * position['quantity']
            fees = (position['entry_price'] * position['quantity'] + last_price * position['quantity']) * self.config.fee_rate
            pnl_net = pnl_gross - fees
            balance = last_price * position['quantity'] - fees
        
        # 5. Calcule métriques
        sell_trades = [t for t in trades if t['type'] == 'sell']
        
        if len(sell_trades) == 0:
            return {
                'final_balance': balance,
                'total_pnl': balance - self.config.initial_balance,
                'roi': ((balance - self.config.initial_balance) / self.config.initial_balance) * 100,
                'total_trades': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'data_points': len(df)
            }
        
        wins = [t for t in sell_trades if t['pnl'] > 0]
        losses = [t for t in sell_trades if t['pnl'] <= 0]
        
        win_rate = (len(wins) / len(sell_trades)) * 100
        avg_pnl = np.mean([t['pnl'] for t in sell_trades])
        best_trade = max([t['pnl'] for t in sell_trades])
        worst_trade = min([t['pnl'] for t in sell_trades])
        
        # Drawdown max
        equity_series = [e['equity'] for e in equity_curve]
        peak = equity_series[0]
        max_dd = 0
        for eq in equity_series:
            if eq > peak:
                peak = eq
            dd = ((peak - eq) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            'final_balance': balance,
            'total_pnl': balance - self.config.initial_balance,
            'roi': ((balance - self.config.initial_balance) / self.config.initial_balance) * 100,
            'total_trades': len(sell_trades),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'max_drawdown': max_dd,
            'sharpe_ratio': self._calculate_sharpe(equity_curve),
            'data_points': len(df),
            'period': f"{df['date'].min()} → {df['date'].max()}",
            'equity_curve': equity_curve,
            'trades': sell_trades
        }
    
    def _calculate_sharpe(self, equity_curve: List[Dict]) -> float:
        """Calcule Sharpe ratio"""
        if len(equity_curve) < 2:
            return 0
        
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
            returns.append(ret)
        
        if len(returns) == 0 or np.std(returns) == 0:
            return 0
        
        return (np.mean(returns) / np.std(returns)) * np.sqrt(252)  # Annualisé
    
    def walk_forward_optimization(
        self,
        strategy_func: Callable,
        param_ranges: Dict,
        train_ratio: float = 0.7,
        n_splits: int = 3
    ) -> Dict:
        """
        Walk-Forward Optimization
        Divise données en train/test et optimise paramètres
        """
        LOG.info(f"🔄 Walk-Forward Optimization ({n_splits} splits)...")
        
        if self.historical_data is None:
            df = self.fetch_historical_data()
        else:
            df = self.historical_data.copy()
        
        df = self.add_indicators(df)
        
        total_len = len(df)
        split_size = total_len // n_splits
        
        results = []
        
        for split in range(n_splits):
            LOG.info(f"   Split {split + 1}/{n_splits}")
            
            # Train période
            train_start = split * split_size
            train_end = int(train_start + split_size * train_ratio)
            
            # Test période
            test_start = train_end
            test_end = min(test_start + split_size * (1 - train_ratio), total_len)
            
            train_df = df.iloc[train_start:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()
            
            # Optimise sur train
            best_params = self._optimize_on_data(train_df, strategy_func, param_ranges)
            
            # Test sur test set
            test_result = self._backtest_on_data(test_df, strategy_func, best_params)
            
            results.append({
                'split': split + 1,
                'best_params': best_params,
                'test_roi': test_result['roi'],
                'test_trades': test_result['total_trades'],
                'test_win_rate': test_result['win_rate']
            })
        
        # Agrège résultats
        avg_roi = np.mean([r['test_roi'] for r in results])
        avg_win_rate = np.mean([r['test_win_rate'] for r in results])
        
        return {
            'walk_forward_results': results,
            'avg_test_roi': avg_roi,
            'avg_win_rate': avg_win_rate,
            'n_splits': n_splits
        }
    
    def _optimize_on_data(self, df, strategy_func, param_ranges) -> Dict:
        """Optimise paramètres sur un dataset"""
        # Simplifié: retourne paramètres moyens
        best_params = {}
        for param, values in param_ranges.items():
            best_params[param] = values[len(values) // 2]
        return best_params
    
    def _backtest_on_data(self, df, strategy_func, params) -> Dict:
        """Backtest sur un dataset spécifique"""
        # Utilise données fournies
        original_data = self.historical_data
        self.historical_data = df
        
        result = self.run_backtest(lambda row: strategy_func(row, params))
        
        self.historical_data = original_data
        return result
    
    def monte_carlo_simulation(self, n_simulations: int = 1000) -> Dict:
        """
        Monte Carlo simulation
        Simule N scénarios en randomisant ordre des trades
        """
        LOG.info(f"🎲 Monte Carlo ({n_simulations} simulations)...")
        
        if self.historical_data is None:
            df = self.fetch_historical_data()
        else:
            df = self.historical_data
        
        # Exécute backtest de référence
        def simple_strategy(row):
            if row['rsi'] < 30:
                return 'buy'
            elif row['rsi'] > 70:
                return 'sell'
            return 'hold'
        
        base_result = self.run_backtest(simple_strategy)
        base_trades = base_result['trades']
        
        if len(base_trades) < 2:
            return {'error': 'Pas assez de trades pour Monte Carlo'}
        
        # Simulations
        final_balances = []
        
        for _ in range(n_simulations):
            # Randomise ordre trades
            shuffled = base_trades.copy()
            np.random.shuffle(shuffled)
            
            balance = self.config.initial_balance
            for trade in shuffled:
                balance += trade['pnl']
            
            final_balances.append(balance)
        
        # Calcule statistiques
        mean_balance = np.mean(final_balances)
        std_balance = np.std(final_balances)
        percentile_5 = np.percentile(final_balances, 5)
        percentile_95 = np.percentile(final_balances, 95)
        
        return {
            'n_simulations': n_simulations,
            'base_final_balance': base_result['final_balance'],
            'mc_mean_balance': mean_balance,
            'mc_std': std_balance,
            'mc_5th_percentile': percentile_5,
            'mc_95th_percentile': percentile_95,
            'confidence_95': (percentile_5 > self.config.initial_balance)
        }


def example_rsi_strategy(row):
    """Exemple de stratégie simple RSI"""
    if pd.notna(row['rsi']):
        if row['rsi'] < 30:
            return 'buy'
        elif row['rsi'] > 70:
            return 'sell'
    return 'hold'


if __name__ == "__main__":
    # Test
    config = BacktestConfig(
        symbol="BTC/USDT",
        timeframe="1h",
        initial_balance=10000,
        days_history=30  # 30 jours pour test rapide
    )
    
    engine = BacktestingEngineReal(config)
    
    # Test backtest simple
    LOG.info("\n" + "=" * 50)
    LOG.info("TEST 1: Backtest Simple")
    LOG.info("=" * 50)
    
    result = engine.run_backtest(example_rsi_strategy)
    
    print(f"\n📊 Résultats Backtest:")
    print(f"   Balance finale: {result['final_balance']:.2f} USDT")
    print(f"   PNL: {result['total_pnl']:.2f} USDT")
    print(f"   ROI: {result['roi']:.2f}%")
    print(f"   Trades: {result['total_trades']}")
    print(f"   Win rate: {result['win_rate']:.1f}%")
    print(f"   Sharpe ratio: {result['sharpe_ratio']:.2f}")
    print(f"   Max drawdown: {result['max_drawdown']:.2f}%")
    
    # Test Monte Carlo
    LOG.info("\n" + "=" * 50)
    LOG.info("TEST 2: Monte Carlo")
    LOG.info("=" * 50)
    
    mc_result = engine.monte_carlo_simulation(n_simulations=100)
    
    print(f"\n🎲 Résultats Monte Carlo:")
    print(f"   Balance moyenne: {mc_result['mc_mean_balance']:.2f} USDT")
    print(f"   5th percentile: {mc_result['mc_5th_percentile']:.2f} USDT")
    print(f"   95th percentile: {mc_result['mc_95th_percentile']:.2f} USDT")
    print(f"   Confiance 95%: {mc_result['confidence_95']}")
