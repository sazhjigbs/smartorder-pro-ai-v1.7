"""
Risk Manager Avancé
Daily loss limit, Drawdown protection, Position sizing intelligent
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskLimits:
    """Limites de risque"""
    max_daily_loss: float = 1000.0  # Perte max par jour
    max_drawdown_percent: float = 15.0  # Drawdown max
    max_position_size_percent: float = 10.0  # % du capital par position
    max_leverage: float = 5.0
    max_correlation: float = 0.7  # Corrélation max entre positions
    max_open_positions: int = 10


class RiskManagerAdvanced:
    """Gestionnaire de risque avancé"""
    
    def __init__(self, initial_capital: float, limits: RiskLimits):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.limits = limits
        
        self.daily_pnl = 0.0
        self.daily_reset_time = time.time()
        
        self.peak_capital = initial_capital
        self.current_drawdown = 0.0
        
        self.open_positions: List[Dict] = []
        self.trade_history: List[Dict] = []
        
        self.is_trading_paused = False
        self.pause_reason = None
    
    def check_can_trade(self) -> Dict:
        """Vérifie si le trading est autorisé"""
        self._reset_daily_stats_if_needed()
        
        # Vérifier daily loss limit
        if self.daily_pnl <= -self.limits.max_daily_loss:
            self.is_trading_paused = True
            self.pause_reason = f"Daily loss limit reached: ${abs(self.daily_pnl):.2f}"
            return {"allowed": False, "reason": self.pause_reason}
        
        # Vérifier drawdown
        self.current_drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        if self.current_drawdown >= self.limits.max_drawdown_percent:
            self.is_trading_paused = True
            self.pause_reason = f"Max drawdown reached: {self.current_drawdown:.2f}%"
            return {"allowed": False, "reason": self.pause_reason}
        
        # Vérifier nombre de positions
        if len(self.open_positions) >= self.limits.max_open_positions:
            return {"allowed": False, "reason": f"Max open positions reached: {len(self.open_positions)}"}
        
        return {"allowed": True, "risk_level": self._calculate_risk_level()}
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss_price: float, risk_percent: float = 1.0) -> Dict:
        """
        Calcule la taille de position optimale
        Basé sur le risque défini (% du capital à risquer)
        """
        risk_amount = self.current_capital * (risk_percent / 100)
        
        # Distance du stop loss
        stop_distance = abs(entry_price - stop_loss_price) / entry_price
        
        if stop_distance == 0:
            return {"quantity": 0, "error": "Invalid stop loss"}
        
        # Calcul de la quantité
        position_value = risk_amount / stop_distance
        quantity = position_value / entry_price
        
        # Vérifier les limites
        max_position_value = self.current_capital * (self.limits.max_position_size_percent / 100)
        if position_value > max_position_value:
            position_value = max_position_value
            quantity = position_value / entry_price
        
        return {
            "quantity": quantity,
            "position_value": position_value,
            "risk_amount": risk_amount,
            "stop_distance_percent": stop_distance * 100
        }
    
    def add_position(self, position: Dict) -> bool:
        """Ajoute une position ouverte"""
        if not self.check_can_trade()["allowed"]:
            return False
        
        self.open_positions.append({
            **position,
            "opened_at": time.time()
        })
        return True
    
    def close_position(self, symbol: str, pnl: float):
        """Ferme une position et met à jour les stats"""
        self.open_positions = [p for p in self.open_positions if p["symbol"] != symbol]
        
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        self.trade_history.append({
            "symbol": symbol,
            "pnl": pnl,
            "timestamp": time.time()
        })
        
        # Vérifier si on doit reprendre le trading
        if self.is_trading_paused and self.daily_pnl > -self.limits.max_daily_loss * 0.8:
            self.is_trading_paused = False
            self.pause_reason = None
    
    def _reset_daily_stats_if_needed(self):
        """Reset des stats journalières"""
        current_time = time.time()
        if current_time - self.daily_reset_time > 86400:  # 24h
            self.daily_pnl = 0.0
            self.daily_reset_time = current_time
            self.is_trading_paused = False
            self.pause_reason = None
    
    def _calculate_risk_level(self) -> RiskLevel:
        """Calcule le niveau de risque actuel"""
        if self.current_drawdown >= self.limits.max_drawdown_percent * 0.8:
            return RiskLevel.CRITICAL
        elif self.current_drawdown >= self.limits.max_drawdown_percent * 0.5:
            return RiskLevel.HIGH
        elif len(self.open_positions) >= self.limits.max_open_positions * 0.7:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_portfolio_stats(self) -> Dict:
        """Stats du portfolio"""
        total_exposure = sum(p.get("value", 0) for p in self.open_positions)
        
        return {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "total_pnl": self.current_capital - self.initial_capital,
            "daily_pnl": self.daily_pnl,
            "current_drawdown": self.current_drawdown,
            "peak_capital": self.peak_capital,
            "open_positions": len(self.open_positions),
            "total_exposure": total_exposure,
            "risk_level": self._calculate_risk_level().value,
            "is_paused": self.is_trading_paused,
            "pause_reason": self.pause_reason
        }


if __name__ == "__main__":
    limits = RiskLimits(
        max_daily_loss=500.0,
        max_drawdown_percent=10.0,
        max_position_size_percent=5.0
    )
    
    manager = RiskManagerAdvanced(initial_capital=10000.0, limits=limits)
    
    # Test position sizing
    pos_size = manager.calculate_position_size(
        symbol="BTCUSDT",
        entry_price=50000,
        stop_loss_price=49000,
        risk_percent=1.0
    )
    print(f"✅ Position size: {pos_size['quantity']:.4f} BTC")
    print(f"📊 Risk: ${pos_size['risk_amount']:.2f}")
    
    # Simuler une perte
    manager.current_capital = 9400  # -600
    manager.daily_pnl = -600
    
    can_trade = manager.check_can_trade()
    print(f"\n🚦 Can trade: {can_trade}")
    print(f"📈 Stats:", manager.get_portfolio_stats())
