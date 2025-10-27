# -*- coding: utf-8 -*-
"""Performance Tracker - Trading metrics"""
import json
from datetime import datetime
from typing import Dict, List

class PerformanceTracker:
    def __init__(self):
        self.trades = []
        self.equity_curve = []
        
    def add_trade(self, trade: Dict):
        """Record a trade"""
        trade['timestamp'] = datetime.now().isoformat()
        self.trades.append(trade)
        
    def get_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {'error': 'No trades'}
        
        wins = [t for t in self.trades if t.get('pnl', 0) > 0]
        losses = [t for t in self.trades if t.get('pnl', 0) < 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        win_rate = len(wins) / len(self.trades) if self.trades else 0
        
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t['pnl'] for t in losses) / len(losses)) if losses else 1
        
        profit_factor = (avg_win * len(wins)) / (avg_loss * len(losses)) if losses else 0
        
        return {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate * 100,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'best_trade': max((t.get('pnl', 0) for t in self.trades), default=0),
            'worst_trade': min((t.get('pnl', 0) for t in self.trades), default=0)
        }
    
    def save(self, filepath: str = 'data/performance.json'):
        """Save performance data"""
        with open(filepath, 'w') as f:
            json.dump({
                'trades': self.trades,
                'metrics': self.get_metrics()
            }, f, indent=2)
