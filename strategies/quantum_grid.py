"""
Quantum Grid - Grid Trading auto-optimisé en temps réel
S'adapte automatiquement aux conditions de marché
"""
import time
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class GridMode(Enum):
    NEUTRAL = "neutral"  # Marché sans tendance
    BULLISH = "bullish"  # Tendance haussière
    BEARISH = "bearish"  # Tendance baissière
    VOLATILE = "volatile"  # Haute volatilité


@dataclass
class QuantumGridConfig:
    symbol: str
    initial_price: float
    total_investment: float
    
    # Paramètres adaptatifs
    grid_levels: int = 10
    grid_spacing_percent: float = 1.0
    
    # Auto-ajustement
    auto_optimize: bool = True
    rebalance_interval: int = 3600  # 1h
    volatility_adjustment: bool = True


class QuantumGrid:
    """Grid Trading avec auto-optimisation quantique"""
    
    def __init__(self, config: QuantumGridConfig):
        self.config = config
        self.grid_orders: List[Dict] = []
        self.filled_orders: List[Dict] = []
        self.current_mode = GridMode.NEUTRAL
        
        self.last_rebalance = time.time()
        self.price_history: List[float] = []
        
        self._initialize_grid()
    
    def _initialize_grid(self):
        """Initialise la grille"""
        base_price = self.config.initial_price
        spacing = self.config.grid_spacing_percent / 100
        
        # Créer niveaux de grille
        for i in range(-self.config.grid_levels // 2, self.config.grid_levels // 2 + 1):
            level_price = base_price * (1 + i * spacing)
            
            order = {
                "level": i,
                "price": level_price,
                "side": "buy" if i < 0 else "sell",
                "quantity": self.config.total_investment / self.config.grid_levels / level_price,
                "filled": False,
                "created_at": time.time()
            }
            self.grid_orders.append(order)
    
    def update(self, current_price: float, market_data: Dict) -> Dict:
        """
        Mise à jour avec prix actuel et données de marché
        Retourne les ordres à placer/modifier
        """
        self.price_history.append(current_price)
        
        # Vérifier les ordres remplis
        actions = self._check_filled_orders(current_price)
        
        # Auto-optimisation
        if self.config.auto_optimize:
            if time.time() - self.last_rebalance > self.config.rebalance_interval:
                self._optimize_grid(market_data)
                self.last_rebalance = time.time()
        
        return {
            "actions": actions,
            "mode": self.current_mode.value,
            "grid_orders": len(self.grid_orders),
            "filled_orders": len(self.filled_orders),
            "current_price": current_price
        }
    
    def _check_filled_orders(self, current_price: float) -> List[Dict]:
        """Vérifie quels ordres sont remplis"""
        actions = []
        
        for order in self.grid_orders:
            if order["filled"]:
                continue
            
            # Buy order rempli si prix descend
            if order["side"] == "buy" and current_price <= order["price"]:
                order["filled"] = True
                order["filled_at"] = time.time()
                self.filled_orders.append(order)
                
                # Créer ordre sell correspondant
                sell_price = order["price"] * (1 + self.config.grid_spacing_percent / 100)
                actions.append({
                    "action": "place_order",
                    "side": "sell",
                    "price": sell_price,
                    "quantity": order["quantity"],
                    "reason": f"Grid level {order['level']} buy filled"
                })
            
            # Sell order rempli si prix monte
            elif order["side"] == "sell" and current_price >= order["price"]:
                order["filled"] = True
                order["filled_at"] = time.time()
                self.filled_orders.append(order)
                
                # Créer ordre buy correspondant
                buy_price = order["price"] * (1 - self.config.grid_spacing_percent / 100)
                actions.append({
                    "action": "place_order",
                    "side": "buy",
                    "price": buy_price,
                    "quantity": order["quantity"],
                    "reason": f"Grid level {order['level']} sell filled"
                })
        
        return actions
    
    def _optimize_grid(self, market_data: Dict):
        """Optimise la grille selon les conditions de marché"""
        if len(self.price_history) < 100:
            return
        
        # Analyser le marché
        volatility = np.std(self.price_history[-100:]) / np.mean(self.price_history[-100:])
        trend = self._detect_trend()
        
        # Ajuster le mode
        if volatility > 0.05:  # 5% de volatilité
            self.current_mode = GridMode.VOLATILE
            # Augmenter l'espacement en volatilité élevée
            if self.config.volatility_adjustment:
                self.config.grid_spacing_percent = min(2.0, self.config.grid_spacing_percent * 1.2)
        elif trend > 0.02:
            self.current_mode = GridMode.BULLISH
            # Biais haussier: plus d'ordres sell
        elif trend < -0.02:
            self.current_mode = GridMode.BEARISH
            # Biais baissier: plus d'ordres buy
        else:
            self.current_mode = GridMode.NEUTRAL
            # Réinitialiser l'espacement
            self.config.grid_spacing_percent = 1.0
        
        print(f"🔄 Grid optimized: Mode={self.current_mode.value}, Spacing={self.config.grid_spacing_percent:.2f}%")
    
    def _detect_trend(self) -> float:
        """Détecte la tendance du marché"""
        if len(self.price_history) < 50:
            return 0.0
        
        recent = self.price_history[-50:]
        sma_20 = np.mean(recent[-20:])
        sma_50 = np.mean(recent)
        
        trend = (sma_20 - sma_50) / sma_50
        return trend
    
    def get_statistics(self) -> Dict:
        """Statistiques de la grille"""
        total_filled = len(self.filled_orders)
        buy_filled = sum(1 for o in self.filled_orders if o["side"] == "buy")
        sell_filled = sum(1 for o in self.filled_orders if o["side"] == "sell")
        
        # Calcul PnL (simplifié)
        pnl = 0.0
        for order in self.filled_orders:
            if order["side"] == "sell":
                pnl += (order["price"] - self.config.initial_price) * order["quantity"]
        
        return {
            "mode": self.current_mode.value,
            "grid_levels": self.config.grid_levels,
            "grid_spacing": self.config.grid_spacing_percent,
            "total_orders": len(self.grid_orders),
            "filled_orders": total_filled,
            "buy_filled": buy_filled,
            "sell_filled": sell_filled,
            "estimated_pnl": pnl,
            "active_since": self.grid_orders[0]["created_at"] if self.grid_orders else None
        }
    
    def rebalance_grid(self, new_center_price: float):
        """Recentre la grille sur un nouveau prix"""
        print(f"🔄 Rebalancing grid to {new_center_price}")
        
        # Annuler les ordres non remplis
        self.grid_orders = [o for o in self.grid_orders if o["filled"]]
        
        # Créer nouvelle grille
        self.config.initial_price = new_center_price
        self._initialize_grid()


# Exemple d'utilisation
if __name__ == "__main__":
    config = QuantumGridConfig(
        symbol="BTCUSDT",
        initial_price=50000,
        total_investment=10000,
        grid_levels=20,
        grid_spacing_percent=0.5,
        auto_optimize=True
    )
    
    grid = QuantumGrid(config)
    
    # Simulation
    prices = [50000 + np.random.randint(-500, 500) + i * 10 for i in range(200)]
    
    for i, price in enumerate(prices):
        market_data = {"volatility": 0.03, "volume": 1000}
        result = grid.update(price, market_data)
        
        if result["actions"]:
            print(f"Step {i}: Price {price:.2f} - {len(result['actions'])} actions")
    
    print("\n📊 Final Stats:")
    stats = grid.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
