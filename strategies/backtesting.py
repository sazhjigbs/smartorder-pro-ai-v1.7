# -*- coding: utf-8 -*-
"""Backtesting Engine"""
import logging
from typing import List, Dict
import pandas as pd

LOG = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.positions = []
        
    def run(self, data: pd.DataFrame, strategy_func) -> Dict:
        """Run backtest on historical data"""
        for i in range(len(data)):
            signal = strategy_func(data.iloc[:i+1])
            if signal['direction'] != 'neutral':
                self._execute_trade(signal, data.iloc[i])
        
        return self.get_metrics()
    
    def _execute_trade(self, signal: Dict, bar):
        price = bar['close']
        size = (self.capital * 0.02) / price  # 2% risk
        
        trade = {
            'timestamp': bar.name,
            'direction': signal['direction'],
            'price': price,
            'size': size,
            'confidence': signal.get('confidence', 0.5)
        }
        self.trades.append(trade)
    
    def get_metrics(self) -> Dict:
        """Calculate backtest metrics"""
        if not self.trades:
            return {'error': 'No trades'}
        
        wins = [t for t in self.trades if t.get('pnl', 0) > 0]
        losses = [t for t in self.trades if t.get('pnl', 0) < 0]
        
        return {
            'total_trades': len(self.trades),
            'win_rate': len(wins) / len(self.trades) if self.trades else 0,
            'total_pnl': sum(t.get('pnl', 0) for t in self.trades),
            'final_capital': self.capital,
            'roi': (self.capital - self.initial_capital) / self.initial_capital
        }
