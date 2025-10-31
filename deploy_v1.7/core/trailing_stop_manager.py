"""
Trailing Stop Loss & Take Profit Manager
Protège les gains et limite les pertes dynamiquement
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class TrailingType(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    BOTH = "both"


@dataclass
class TrailingConfig:
    """Configuration du trailing stop"""
    symbol: str
    side: str  # "buy" ou "sell"
    entry_price: float
    current_price: float
    trailing_type: TrailingType
    
    # Stop Loss Trailing
    stop_loss_percent: float = 2.0  # 2% de perte max
    trailing_stop_percent: float = 1.0  # Trail de 1%
    
    # Take Profit Trailing
    take_profit_percent: float = 5.0  # 5% de gain
    trailing_profit_percent: float = 1.5  # Trail de 1.5%
    
    # État
    highest_price: Optional[float] = None
    lowest_price: Optional[float] = None
    stop_price: Optional[float] = None
    activated: bool = False


class TrailingStopManager:
    """Gestionnaire de Trailing Stop Loss & Take Profit"""
    
    def __init__(self):
        self.active_trails: Dict[str, TrailingConfig] = {}
        self.triggered_trails: List[Dict] = []
        
    def add_trailing_stop(self, config: TrailingConfig) -> str:
        """Ajoute un trailing stop"""
        trail_id = f"{config.symbol}_{int(time.time()*1000)}"
        
        # Initialisation des prix extrêmes
        if config.side == "buy":
            config.highest_price = config.entry_price
            config.lowest_price = config.entry_price
        else:
            config.highest_price = config.entry_price
            config.lowest_price = config.entry_price
            
        self.active_trails[trail_id] = config
        return trail_id
    
    def update_price(self, trail_id: str, current_price: float) -> Dict:
        """
        Met à jour le prix et vérifie si le trailing est déclenché
        
        Returns:
            Dict avec 'triggered', 'action', 'price', 'reason'
        """
        if trail_id not in self.active_trails:
            return {"triggered": False, "error": "Trail ID not found"}
        
        config = self.active_trails[trail_id]
        config.current_price = current_price
        
        result = {
            "triggered": False,
            "action": None,
            "price": current_price,
            "reason": None,
            "trail_id": trail_id
        }
        
        if config.side == "buy":
            result = self._check_long_position(config)
        else:
            result = self._check_short_position(config)
        
        if result["triggered"]:
            self.triggered_trails.append({
                "trail_id": trail_id,
                "config": config,
                "result": result,
                "timestamp": time.time()
            })
            del self.active_trails[trail_id]
        
        return result
    
    def _check_long_position(self, config: TrailingConfig) -> Dict:
        """Vérifie trailing pour position LONG"""
        current = config.current_price
        entry = config.entry_price
        
        # Mise à jour du prix le plus haut
        if config.highest_price is None or current > config.highest_price:
            config.highest_price = current
        
        profit_percent = ((current - entry) / entry) * 100
        
        # STOP LOSS CLASSIQUE (si prix descend en dessous)
        if config.trailing_type in [TrailingType.STOP_LOSS, TrailingType.BOTH]:
            stop_loss_price = entry * (1 - config.stop_loss_percent / 100)
            
            if current <= stop_loss_price:
                return {
                    "triggered": True,
                    "action": "SELL",
                    "price": current,
                    "reason": f"Stop Loss triggered at {config.stop_loss_percent}% loss",
                    "trail_id": None
                }
        
        # TRAILING STOP LOSS (après gain)
        if config.trailing_type in [TrailingType.STOP_LOSS, TrailingType.BOTH]:
            if profit_percent > 0:  # En profit
                trailing_stop_price = config.highest_price * (1 - config.trailing_stop_percent / 100)
                
                if current <= trailing_stop_price:
                    return {
                        "triggered": True,
                        "action": "SELL",
                        "price": current,
                        "reason": f"Trailing Stop Loss triggered (secured profit, -{config.trailing_stop_percent}% from peak)",
                        "trail_id": None
                    }
        
        # TAKE PROFIT TRAILING
        if config.trailing_type in [TrailingType.TAKE_PROFIT, TrailingType.BOTH]:
            if profit_percent >= config.take_profit_percent:
                config.activated = True
                
            if config.activated:
                trailing_tp_price = config.highest_price * (1 - config.trailing_profit_percent / 100)
                
                if current <= trailing_tp_price:
                    return {
                        "triggered": True,
                        "action": "SELL",
                        "price": current,
                        "reason": f"Trailing Take Profit triggered (secured {profit_percent:.2f}% gain)",
                        "trail_id": None
                    }
        
        return {"triggered": False}
    
    def _check_short_position(self, config: TrailingConfig) -> Dict:
        """Vérifie trailing pour position SHORT"""
        current = config.current_price
        entry = config.entry_price
        
        # Mise à jour du prix le plus bas
        if config.lowest_price is None or current < config.lowest_price:
            config.lowest_price = current
        
        profit_percent = ((entry - current) / entry) * 100
        
        # STOP LOSS CLASSIQUE
        if config.trailing_type in [TrailingType.STOP_LOSS, TrailingType.BOTH]:
            stop_loss_price = entry * (1 + config.stop_loss_percent / 100)
            
            if current >= stop_loss_price:
                return {
                    "triggered": True,
                    "action": "BUY",
                    "price": current,
                    "reason": f"Stop Loss triggered at {config.stop_loss_percent}% loss",
                    "trail_id": None
                }
        
        # TRAILING STOP LOSS
        if config.trailing_type in [TrailingType.STOP_LOSS, TrailingType.BOTH]:
            if profit_percent > 0:
                trailing_stop_price = config.lowest_price * (1 + config.trailing_stop_percent / 100)
                
                if current >= trailing_stop_price:
                    return {
                        "triggered": True,
                        "action": "BUY",
                        "price": current,
                        "reason": f"Trailing Stop Loss triggered (secured profit, +{config.trailing_stop_percent}% from bottom)",
                        "trail_id": None
                    }
        
        # TAKE PROFIT TRAILING
        if config.trailing_type in [TrailingType.TAKE_PROFIT, TrailingType.BOTH]:
            if profit_percent >= config.take_profit_percent:
                config.activated = True
                
            if config.activated:
                trailing_tp_price = config.lowest_price * (1 + config.trailing_profit_percent / 100)
                
                if current >= trailing_tp_price:
                    return {
                        "triggered": True,
                        "action": "BUY",
                        "price": current,
                        "reason": f"Trailing Take Profit triggered (secured {profit_percent:.2f}% gain)",
                        "trail_id": None
                    }
        
        return {"triggered": False}
    
    def get_active_trails(self) -> Dict:
        """Retourne tous les trailing stops actifs"""
        return {
            trail_id: {
                "symbol": config.symbol,
                "side": config.side,
                "entry_price": config.entry_price,
                "current_price": config.current_price,
                "highest_price": config.highest_price,
                "lowest_price": config.lowest_price,
                "type": config.trailing_type.value,
                "activated": config.activated
            }
            for trail_id, config in self.active_trails.items()
        }
    
    def remove_trailing(self, trail_id: str) -> bool:
        """Supprime un trailing stop"""
        if trail_id in self.active_trails:
            del self.active_trails[trail_id]
            return True
        return False
    
    def get_statistics(self) -> Dict:
        """Statistiques des trailing stops"""
        total_triggered = len(self.triggered_trails)
        wins = sum(1 for t in self.triggered_trails if "secured" in t["result"]["reason"].lower())
        losses = sum(1 for t in self.triggered_trails if "loss" in t["result"]["reason"].lower())
        
        return {
            "active_trails": len(self.active_trails),
            "total_triggered": total_triggered,
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / total_triggered * 100) if total_triggered > 0 else 0
        }


# Exemple d'utilisation
if __name__ == "__main__":
    manager = TrailingStopManager()
    
    # Position LONG sur BTC
    config = TrailingConfig(
        symbol="BTCUSDT",
        side="buy",
        entry_price=50000,
        current_price=50000,
        trailing_type=TrailingType.BOTH,
        stop_loss_percent=2.0,
        trailing_stop_percent=1.0,
        take_profit_percent=5.0,
        trailing_profit_percent=1.5
    )
    
    trail_id = manager.add_trailing_stop(config)
    print(f"✅ Trailing stop créé: {trail_id}")
    
    # Simulation de mouvement de prix
    prices = [50500, 51000, 52000, 53000, 52500, 52000]
    
    for price in prices:
        result = manager.update_price(trail_id, price)
        print(f"Prix: {price} - Triggered: {result['triggered']}")
        if result["triggered"]:
            print(f"🚨 ACTION: {result['action']} - Reason: {result['reason']}")
            break
    
    print("\n📊 Stats:", manager.get_statistics())
