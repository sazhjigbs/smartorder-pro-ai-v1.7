# -*- coding: utf-8 -*-
"""
Risk Manager
Gestion professionnelle du risque pour trading

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import logging
from typing import Dict, Optional
from datetime import datetime

LOG = logging.getLogger(__name__)


class RiskManager:
    """
    Gestionnaire de risque professionnel
    
    Features:
    - Position sizing (Kelly Criterion, Fixed %, ATR-based)
    - Stop-loss dynamique
    - Take-profit automatique
    - Max drawdown protection
    - Risk per trade
    - Portfolio heat (total risk exposure)
    """
    
    def __init__(self,
                 max_risk_per_trade: float = 0.02,
                 max_portfolio_risk: float = 0.10,
                 max_drawdown: float = 0.15,
                 use_kelly_criterion: bool = False,
                 kelly_fraction: float = 0.25):
        """
        Initialize Risk Manager
        
        Args:
            max_risk_per_trade: Max % of capital to risk per trade (default 2%)
            max_portfolio_risk: Max % of capital at risk simultaneously (default 10%)
            max_drawdown: Max allowed drawdown before stopping (default 15%)
            use_kelly_criterion: Use Kelly for position sizing
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly)
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown = max_drawdown
        self.use_kelly_criterion = use_kelly_criterion
        self.kelly_fraction = kelly_fraction
        
        # Track state
        self.current_drawdown = 0.0
        self.peak_equity = 0.0
        self.total_risk_exposure = 0.0
        
        LOG.info(f"Risk Manager initialized (max_risk={max_risk_per_trade*100}%, max_dd={max_drawdown*100}%)")
    
    def calculate_position_size(self,
                                 account_balance: float,
                                 entry_price: float,
                                 stop_loss_price: float,
                                 win_rate: Optional[float] = None,
                                 avg_win: Optional[float] = None,
                                 avg_loss: Optional[float] = None) -> Dict:
        """
        Calculate position size based on risk parameters
        
        Args:
            account_balance: Total account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            win_rate: Historical win rate (for Kelly)
            avg_win: Average win size (for Kelly)
            avg_loss: Average loss size (for Kelly)
        
        Returns:
            {
                'position_size': quantity to trade,
                'risk_amount': dollar amount at risk,
                'risk_percent': % of account at risk,
                'method': 'fixed' or 'kelly'
            }
        """
        # Check if we can take more risk
        if self.total_risk_exposure >= self.max_portfolio_risk:
            LOG.warning(f"Portfolio risk limit reached ({self.total_risk_exposure*100:.1f}%)")
            return {
                'position_size': 0,
                'risk_amount': 0,
                'risk_percent': 0,
                'method': 'blocked',
                'reason': 'Max portfolio risk reached'
            }
        
        # Check drawdown
        if self.current_drawdown >= self.max_drawdown:
            LOG.error(f"Max drawdown reached ({self.current_drawdown*100:.1f}%)")
            return {
                'position_size': 0,
                'risk_amount': 0,
                'risk_percent': 0,
                'method': 'blocked',
                'reason': 'Max drawdown exceeded'
            }
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            LOG.error("Invalid stop loss - same as entry price")
            return {'position_size': 0, 'risk_amount': 0, 'risk_percent': 0, 'method': 'error'}
        
        # Use Kelly Criterion if data available
        if self.use_kelly_criterion and win_rate and avg_win and avg_loss:
            kelly_fraction_value = self._calculate_kelly(win_rate, avg_win, avg_loss)
            risk_amount = account_balance * kelly_fraction_value * self.kelly_fraction
            method = 'kelly'
        else:
            # Fixed % risk
            risk_amount = account_balance * self.max_risk_per_trade
            method = 'fixed'
        
        # Calculate position size
        position_size = risk_amount / risk_per_unit
        
        # Risk percent
        risk_percent = (risk_amount / account_balance)
        
        LOG.info(f"Position size: {position_size:.4f} (risk: ${risk_amount:.2f}, {risk_percent*100:.2f}%, method: {method})")
        
        return {
            'position_size': position_size,
            'risk_amount': risk_amount,
            'risk_percent': risk_percent,
            'method': method,
            'risk_per_unit': risk_per_unit
        }
    
    def _calculate_kelly(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion
        
        Formula: K = W - (1-W)/R
        Where:
        - W = win rate
        - R = avg_win / avg_loss (win/loss ratio)
        
        Returns:
            Optimal fraction of capital to risk
        """
        if avg_loss == 0:
            return 0
        
        win_loss_ratio = avg_win / avg_loss
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Never risk more than max
        kelly = max(0, min(kelly, self.max_risk_per_trade))
        
        return kelly
    
    def calculate_stop_loss(self,
                            entry_price: float,
                            atr: float,
                            side: str = 'long',
                            atr_multiplier: float = 2.0) -> float:
        """
        Calculate dynamic stop-loss based on ATR
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            side: 'long' or 'short'
            atr_multiplier: ATR multiplier (default 2.0)
        
        Returns:
            Stop loss price
        """
        stop_distance = atr * atr_multiplier
        
        if side.lower() == 'long':
            stop_loss = entry_price - stop_distance
        else:  # short
            stop_loss = entry_price + stop_distance
        
        LOG.info(f"Stop loss calculated: {stop_loss:.2f} (ATR: {atr:.2f}, distance: {stop_distance:.2f})")
        
        return stop_loss
    
    def calculate_take_profit(self,
                              entry_price: float,
                              stop_loss: float,
                              side: str = 'long',
                              risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take-profit based on risk/reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            risk_reward_ratio: Target R:R (default 2:1)
        
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if side.lower() == 'long':
            take_profit = entry_price + reward
        else:  # short
            take_profit = entry_price - reward
        
        LOG.info(f"Take profit: {take_profit:.2f} (R:R = {risk_reward_ratio}:1, reward: {reward:.2f})")
        
        return take_profit
    
    def update_drawdown(self, current_equity: float):
        """
        Update drawdown tracking
        
        Args:
            current_equity: Current account equity
        """
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.current_drawdown = 0.0
        else:
            # Calculate drawdown
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        
        if self.current_drawdown > 0.05:  # Warning at 5%
            LOG.warning(f"Drawdown: {self.current_drawdown*100:.2f}%")
    
    def add_position_risk(self, risk_amount: float, account_balance: float):
        """
        Add position to total risk exposure
        
        Args:
            risk_amount: Dollar amount at risk
            account_balance: Total account balance
        """
        risk_percent = risk_amount / account_balance
        self.total_risk_exposure += risk_percent
        
        LOG.info(f"Portfolio risk: {self.total_risk_exposure*100:.2f}%")
    
    def remove_position_risk(self, risk_amount: float, account_balance: float):
        """
        Remove position from total risk exposure
        
        Args:
            risk_amount: Dollar amount at risk
            account_balance: Total account balance
        """
        risk_percent = risk_amount / account_balance
        self.total_risk_exposure = max(0, self.total_risk_exposure - risk_percent)
        
        LOG.info(f"Portfolio risk: {self.total_risk_exposure*100:.2f}%")
    
    def can_open_position(self) -> bool:
        """
        Check if we can open a new position
        
        Returns:
            True if position can be opened
        """
        # Check portfolio risk
        if self.total_risk_exposure >= self.max_portfolio_risk:
            LOG.warning("Cannot open position: max portfolio risk")
            return False
        
        # Check drawdown
        if self.current_drawdown >= self.max_drawdown:
            LOG.error("Cannot open position: max drawdown exceeded")
            return False
        
        return True
    
    def get_risk_status(self) -> Dict:
        """
        Get current risk status
        
        Returns:
            Risk status dictionary
        """
        return {
            'portfolio_risk': self.total_risk_exposure,
            'portfolio_risk_percent': self.total_risk_exposure * 100,
            'current_drawdown': self.current_drawdown,
            'current_drawdown_percent': self.current_drawdown * 100,
            'peak_equity': self.peak_equity,
            'can_trade': self.can_open_position(),
            'risk_capacity': self.max_portfolio_risk - self.total_risk_exposure,
            'drawdown_buffer': self.max_drawdown - self.current_drawdown
        }


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize risk manager
    risk_mgr = RiskManager(
        max_risk_per_trade=0.02,  # 2%
        max_portfolio_risk=0.10,  # 10%
        max_drawdown=0.15  # 15%
    )
    
    # Test position sizing
    print("\nTest 1: Position Sizing")
    print("=" * 50)
    
    result = risk_mgr.calculate_position_size(
        account_balance=10000,
        entry_price=50000,
        stop_loss_price=49000  # $1000 risk per unit
    )
    
    print(f"Position size: {result['position_size']:.4f}")
    print(f"Risk amount: ${result['risk_amount']:.2f}")
    print(f"Risk percent: {result['risk_percent']*100:.2f}%")
    
    # Test stop-loss/take-profit
    print("\nTest 2: Stop-Loss & Take-Profit")
    print("=" * 50)
    
    entry = 50000
    atr = 500
    
    stop_loss = risk_mgr.calculate_stop_loss(entry, atr, side='long')
    take_profit = risk_mgr.calculate_take_profit(entry, stop_loss, side='long', risk_reward_ratio=2.0)
    
    print(f"Entry: ${entry}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Take Profit: ${take_profit:.2f}")
    print(f"Risk: ${entry - stop_loss:.2f}")
    print(f"Reward: ${take_profit - entry:.2f}")
    
    # Test risk status
    print("\nTest 3: Risk Status")
    print("=" * 50)
    
    risk_mgr.add_position_risk(200, 10000)  # 2%
    risk_mgr.update_drawdown(9500)  # -5% drawdown
    
    status = risk_mgr.get_risk_status()
    print(f"Portfolio risk: {status['portfolio_risk_percent']:.2f}%")
    print(f"Current drawdown: {status['current_drawdown_percent']:.2f}%")
    print(f"Can trade: {status['can_trade']}")
