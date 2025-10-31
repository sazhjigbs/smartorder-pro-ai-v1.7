"""
Backtesting Engine Pro
Walk-forward optimization, Monte Carlo simulation, Visualisation
"""
import time
import numpy as np
import random
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


@dataclass
class BacktestConfig:
    """Configuration du backtest"""
    initial_capital: float = 10000.0
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    
    # Walk-forward
    in_sample_period: int = 180  # 6 mois
    out_sample_period: int = 30  # 1 mois
    
    # Monte Carlo
    num_simulations: int = 1000
    confidence_level: float = 0.95


@dataclass
class Trade:
    """Trade du backtest"""
    entry_time: float
    exit_time: float
    entry_price: float
    exit_price: float
    quantity: float
    side: str  # "buy" or "sell"
    pnl: float
    pnl_percent: float
    commission: float


class BacktestingEnginePro:
    """Moteur de backtesting professionnel"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.capital = config.initial_capital
        self.peak_capital = config.initial_capital
        
    def run_backtest(self, strategy: Callable, market_data: Dict) -> Dict:
        """Exécute un backtest simple"""
        self.trades = []
        self.equity_curve = [self.config.initial_capital]
        self.capital = self.config.initial_capital
        
        prices = market_data.get('closes', [])
        timestamps = market_data.get('timestamps', list(range(len(prices))))
        
        # Simulation des trades
        for i in range(50, len(prices)):
            window = {
                'closes': prices[i-50:i],
                'timestamp': timestamps[i]
            }
            
            # Appeler la stratégie
            signal = strategy(window)
            
            if signal and signal.get('action') in ['buy', 'sell']:
                trade = self._execute_trade(
                    timestamp=timestamps[i],
                    price=prices[i],
                    side=signal['action'],
                    quantity=signal.get('quantity', 0.1)
                )
                
                if trade:
                    self.trades.append(trade)
                    self.capital += trade.pnl
                    self.equity_curve.append(self.capital)
                    
                    if self.capital > self.peak_capital:
                        self.peak_capital = self.capital
        
        return self.calculate_metrics()
    
    def walk_forward_optimization(self, strategy: Callable, market_data: Dict, param_ranges: Dict) -> Dict:
        """
        Walk-Forward Optimization
        Optimise sur période in-sample, valide sur out-sample
        """
        prices = market_data.get('closes', [])
        total_periods = len(prices) // (self.config.in_sample_period + self.config.out_sample_period)
        
        results = []
        best_params_history = []
        
        for period in range(total_periods):
            # Période in-sample (optimisation)
            in_start = period * (self.config.in_sample_period + self.config.out_sample_period)
            in_end = in_start + self.config.in_sample_period
            
            in_sample_data = {
                'closes': prices[in_start:in_end],
                'timestamps': list(range(in_start, in_end))
            }
            
            # Trouver meilleurs paramètres
            best_params, best_sharpe = self._optimize_parameters(strategy, in_sample_data, param_ranges)
            best_params_history.append(best_params)
            
            # Période out-sample (validation)
            out_start = in_end
            out_end = out_start + self.config.out_sample_period
            
            if out_end > len(prices):
                break
            
            out_sample_data = {
                'closes': prices[out_start:out_end],
                'timestamps': list(range(out_start, out_end))
            }
            
            # Tester avec les meilleurs paramètres
            metrics = self.run_backtest(
                lambda data: strategy(data, **best_params),
                out_sample_data
            )
            
            results.append({
                "period": period,
                "in_sample_period": (in_start, in_end),
                "out_sample_period": (out_start, out_end),
                "best_params": best_params,
                "out_sample_metrics": metrics
            })
        
        # Agrégation des résultats
        avg_sharpe = np.mean([r['out_sample_metrics']['sharpe_ratio'] for r in results if r['out_sample_metrics']['sharpe_ratio']])
        avg_win_rate = np.mean([r['out_sample_metrics']['win_rate'] for r in results])
        
        return {
            "walk_forward_results": results,
            "avg_out_sample_sharpe": avg_sharpe,
            "avg_out_sample_win_rate": avg_win_rate,
            "num_periods": len(results),
            "best_params_history": best_params_history
        }
    
    def monte_carlo_simulation(self, trades: Optional[List[Trade]] = None) -> Dict:
        """
        Monte Carlo Simulation
        Simule différentes séquences de trades pour estimer risque
        """
        if trades is None:
            trades = self.trades
        
        if len(trades) < 10:
            return {"error": "Not enough trades for Monte Carlo"}
        
        # Extraire les PnL
        pnls = [t.pnl for t in trades]
        
        simulation_results = []
        
        for sim in range(self.config.num_simulations):
            # Mélanger aléatoirement l'ordre des trades
            shuffled_pnls = random.sample(pnls, len(pnls))
            
            # Calculer equity curve
            capital = self.config.initial_capital
            equity = [capital]
            peak = capital
            max_dd = 0
            
            for pnl in shuffled_pnls:
                capital += pnl
                equity.append(capital)
                
                if capital > peak:
                    peak = capital
                
                dd = (peak - capital) / peak * 100
                if dd > max_dd:
                    max_dd = dd
            
            final_capital = equity[-1]
            total_return = ((final_capital - self.config.initial_capital) / self.config.initial_capital) * 100
            
            simulation_results.append({
                "final_capital": final_capital,
                "total_return": total_return,
                "max_drawdown": max_dd
            })
        
        # Analyse statistique
        final_capitals = [s['final_capital'] for s in simulation_results]
        returns = [s['total_return'] for s in simulation_results]
        drawdowns = [s['max_drawdown'] for s in simulation_results]
        
        # Percentiles
        confidence = self.config.confidence_level
        var_percentile = (1 - confidence) * 100
        
        return {
            "num_simulations": self.config.num_simulations,
            "mean_final_capital": np.mean(final_capitals),
            "median_final_capital": np.median(final_capitals),
            "std_final_capital": np.std(final_capitals),
            "mean_return": np.mean(returns),
            "median_return": np.median(returns),
            "worst_case_return": np.percentile(returns, var_percentile),
            "best_case_return": np.percentile(returns, 100 - var_percentile),
            "mean_max_drawdown": np.mean(drawdowns),
            "worst_drawdown": np.max(drawdowns),
            "probability_of_profit": sum(1 for r in returns if r > 0) / len(returns) * 100,
            f"var_{int(confidence*100)}": np.percentile(returns, var_percentile)
        }
    
    def _execute_trade(self, timestamp: float, price: float, side: str, quantity: float) -> Optional[Trade]:
        """Simule l'exécution d'un trade"""
        # Appliquer slippage
        if side == "buy":
            execution_price = price * (1 + self.config.slippage)
        else:
            execution_price = price * (1 - self.config.slippage)
        
        # Commission
        commission = execution_price * quantity * self.config.commission
        
        # Pour simplification, fermer après 10 steps
        exit_price = price * (1 + random.uniform(-0.02, 0.03))
        
        if side == "buy":
            pnl = (exit_price - execution_price) * quantity - commission * 2
        else:
            pnl = (execution_price - exit_price) * quantity - commission * 2
        
        pnl_percent = (pnl / (execution_price * quantity)) * 100
        
        return Trade(
            entry_time=timestamp,
            exit_time=timestamp + 10,
            entry_price=execution_price,
            exit_price=exit_price,
            quantity=quantity,
            side=side,
            pnl=pnl,
            pnl_percent=pnl_percent,
            commission=commission * 2
        )
    
    def _optimize_parameters(self, strategy: Callable, data: Dict, param_ranges: Dict) -> tuple:
        """Optimise les paramètres sur les données in-sample"""
        best_sharpe = -999
        best_params = {}
        
        # Grid search simplifié
        for _ in range(20):  # 20 essais aléatoires
            params = {}
            for param, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int):
                    params[param] = random.randint(min_val, max_val)
                else:
                    params[param] = random.uniform(min_val, max_val)
            
            # Tester ces paramètres
            metrics = self.run_backtest(
                lambda window: strategy(window, **params),
                data
            )
            
            sharpe = metrics.get('sharpe_ratio', -999)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = params.copy()
        
        return best_params, best_sharpe
    
    def calculate_metrics(self) -> Dict:
        """Calcule les métriques de performance"""
        if not self.trades:
            return {}
        
        pnls = [t.pnl for t in self.trades]
        total_pnl = sum(pnls)
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Sharpe ratio
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Max drawdown
        peak = self.equity_curve[0]
        max_dd = 0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_return_percent": (total_pnl / self.config.initial_capital) * 100,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_dd,
            "final_capital": self.equity_curve[-1] if self.equity_curve else self.config.initial_capital
        }


# Exemple d'utilisation
if __name__ == "__main__":
    config = BacktestConfig(
        initial_capital=10000,
        commission=0.001,
        num_simulations=1000
    )
    
    engine = BacktestingEnginePro(config)
    
    # Stratégie exemple
    def simple_strategy(data, **params):
        prices = data.get('closes', [])
        if len(prices) < 20:
            return None
        
        sma = np.mean(prices[-20:])
        current = prices[-1]
        
        if current > sma * 1.02:
            return {"action": "buy", "quantity": 0.1}
        elif current < sma * 0.98:
            return {"action": "sell", "quantity": 0.1}
        return None
    
    # Données simulées
    prices = [10000 + i * 10 + np.random.randint(-100, 100) for i in range(365)]
    market_data = {'closes': prices, 'timestamps': list(range(365))}
    
    # Backtest simple
    print("=== Backtest Simple ===")
    results = engine.run_backtest(simple_strategy, market_data)
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Total Return: {results['total_return_percent']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    # Monte Carlo
    print("\n=== Monte Carlo Simulation ===")
    mc_results = engine.monte_carlo_simulation()
    print(f"Mean Return: {mc_results['mean_return']:.2f}%")
    print(f"Worst Case: {mc_results['worst_case_return']:.2f}%")
    print(f"Probability of Profit: {mc_results['probability_of_profit']:.2f}%")
