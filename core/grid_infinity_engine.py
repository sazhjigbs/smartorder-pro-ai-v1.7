#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Infinity Grid Engine
=========================================
Grid Trading illimité style KuCoin
by MAIGA ABOUBACAR

Features:
- Grilles géométriques illimitées
- Trailing min price automatique
- Auto-expansion des grilles
- Profit compounding
- Multi-coins support
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

LOG = logging.getLogger("grid_infinity")
LOG.setLevel(logging.INFO)

class GridMode(Enum):
    """Mode de grille"""
    ARITHMETIC = "arithmetic"  # Écarts fixes
    GEOMETRIC = "geometric"    # Écarts en pourcentage (recommandé)

@dataclass
class GridOrder:
    """Ordre de grille"""
    order_id: str
    coin: str
    side: str  # buy | sell
    price: float
    quantity: float
    grid_level: int
    status: str = "pending"  # pending | filled | cancelled
    filled_at: Optional[str] = None
    profit: float = 0.0

@dataclass
class GridConfig:
    """Configuration d'une grille"""
    coin: str
    mode: GridMode = GridMode.GEOMETRIC
    min_price: float = 0.0
    max_price: float = 0.0
    grid_count: int = 20
    profit_per_grid: float = 1.0  # % profit par grille
    investment: float = 100.0  # Capital alloué
    trailing_enabled: bool = True
    auto_expand: bool = True
    compound_profit: bool = True
    enabled: bool = True

class GridInfinityEngine:
    """
    Infinity Grid Trading Engine
    
    Style KuCoin avec:
    - Grilles géométriques illimitées
    - Trailing min price
    - Auto-expansion
    - Compounding
    """
    
    def __init__(self, config_dir: str = "config"):
        """Initialize Grid Infinity Engine"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "grid_infinity_config.json"
        self.orders_file = self.config_dir / "grid_orders.json"
        self.stats_file = self.config_dir / "grid_stats.json"
        
        # Active grids
        self.grids: Dict[str, GridConfig] = {}
        self.orders: Dict[str, List[GridOrder]] = {}  # coin -> orders
        self.stats: Dict[str, Dict] = {}  # coin -> stats
        
        self._load_config()
        self._load_orders()
        
        LOG.info("✅ Grid Infinity Engine initialized")
    
    def _load_config(self):
        """Charge la configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for coin, grid_data in data.items():
                        grid_data['mode'] = GridMode(grid_data['mode'])
                        self.grids[coin] = GridConfig(**grid_data)
                LOG.info(f"✅ Loaded {len(self.grids)} grid configs")
            except Exception as e:
                LOG.error(f"❌ Error loading config: {e}")
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            data = {}
            for coin, grid in self.grids.items():
                grid_dict = asdict(grid)
                grid_dict['mode'] = grid.mode.value
                data[coin] = grid_dict
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            LOG.info("✅ Grid config saved")
        except Exception as e:
            LOG.error(f"❌ Error saving config: {e}")
    
    def _load_orders(self):
        """Charge les ordres de grille"""
        if self.orders_file.exists():
            try:
                with open(self.orders_file, 'r') as f:
                    data = json.load(f)
                    for coin, orders_data in data.items():
                        self.orders[coin] = [GridOrder(**o) for o in orders_data]
                LOG.info(f"✅ Loaded grid orders for {len(self.orders)} coins")
            except Exception as e:
                LOG.error(f"❌ Error loading orders: {e}")
    
    def _save_orders(self):
        """Sauvegarde les ordres"""
        try:
            data = {}
            for coin, orders in self.orders.items():
                data[coin] = [asdict(o) for o in orders]
            
            with open(self.orders_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOG.error(f"❌ Error saving orders: {e}")
    
    def create_grid(self, coin: str, current_price: float, 
                   investment: float = 100.0, grid_count: int = 20,
                   profit_per_grid: float = 1.0, mode: GridMode = GridMode.GEOMETRIC) -> bool:
        """
        Crée une nouvelle grille infinie
        
        Args:
            coin: Symbol du coin
            current_price: Prix actuel
            investment: Capital à allouer
            grid_count: Nombre de grilles
            profit_per_grid: % profit par grille
            mode: ARITHMETIC ou GEOMETRIC
        """
        if coin in self.grids:
            LOG.warning(f"⚠️ Grid already exists for {coin}")
            return False
        
        # Calculate price range (±30% autour du prix actuel)
        min_price = current_price * 0.7
        max_price = current_price * 1.3
        
        # Create grid config
        grid = GridConfig(
            coin=coin,
            mode=mode,
            min_price=min_price,
            max_price=max_price,
            grid_count=grid_count,
            profit_per_grid=profit_per_grid,
            investment=investment,
            trailing_enabled=True,
            auto_expand=True,
            compound_profit=True,
            enabled=True
        )
        
        self.grids[coin] = grid
        
        # Initialize orders
        self._initialize_grid_orders(coin, current_price)
        
        # Initialize stats
        self.stats[coin] = {
            "total_profits": 0.0,
            "total_trades": 0,
            "filled_buy_orders": 0,
            "filled_sell_orders": 0,
            "current_position": 0.0,
            "avg_buy_price": 0.0,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_config()
        self._save_orders()
        
        LOG.info(f"✅ Created infinity grid for {coin}")
        LOG.info(f"   Range: ${min_price:.2f} - ${max_price:.2f}")
        LOG.info(f"   Grid count: {grid_count}")
        LOG.info(f"   Profit/grid: {profit_per_grid}%")
        
        return True
    
    def _initialize_grid_orders(self, coin: str, current_price: float):
        """Initialise les ordres de grille"""
        grid = self.grids[coin]
        
        # Calculate grid levels
        grid_prices = self._calculate_grid_levels(
            grid.min_price,
            grid.max_price,
            grid.grid_count,
            grid.mode
        )
        
        # Calculate quantity per order
        quantity_per_order = grid.investment / (grid.grid_count * current_price)
        
        # Create orders
        orders = []
        for i, price in enumerate(grid_prices):
            # Buy orders below current price
            if price < current_price:
                orders.append(GridOrder(
                    order_id=f"{coin}_buy_{i}",
                    coin=coin,
                    side="buy",
                    price=price,
                    quantity=quantity_per_order,
                    grid_level=i,
                    status="pending"
                ))
            # Sell orders above current price
            elif price > current_price:
                orders.append(GridOrder(
                    order_id=f"{coin}_sell_{i}",
                    coin=coin,
                    side="sell",
                    price=price,
                    quantity=quantity_per_order,
                    grid_level=i,
                    status="pending"
                ))
        
        self.orders[coin] = orders
        LOG.info(f"✅ Initialized {len(orders)} grid orders for {coin}")
    
    def _calculate_grid_levels(self, min_price: float, max_price: float, 
                               count: int, mode: GridMode) -> List[float]:
        """
        Calcule les niveaux de prix de la grille
        
        Args:
            min_price: Prix minimum
            max_price: Prix maximum
            count: Nombre de grilles
            mode: ARITHMETIC ou GEOMETRIC
        
        Returns:
            Liste des prix de grille
        """
        if mode == GridMode.ARITHMETIC:
            # Écarts fixes
            step = (max_price - min_price) / count
            return [min_price + (i * step) for i in range(count + 1)]
        else:
            # Écarts géométriques (recommandé)
            ratio = (max_price / min_price) ** (1 / count)
            return [min_price * (ratio ** i) for i in range(count + 1)]
    
    def update_price(self, coin: str, current_price: float) -> List[Dict]:
        """
        Met à jour la grille avec le nouveau prix
        
        Gère:
        - Trailing min price
        - Auto-expansion
        - Fill detection
        
        Returns:
            Liste des ordres à exécuter
        """
        if coin not in self.grids:
            return []
        
        grid = self.grids[coin]
        if not grid.enabled:
            return []
        
        actions = []
        
        # Trailing min price
        if grid.trailing_enabled and current_price < grid.min_price:
            LOG.info(f"🔄 Trailing min price for {coin}: ${grid.min_price:.2f} -> ${current_price:.2f}")
            grid.min_price = current_price
            grid.max_price = current_price * 1.3
            self._rebalance_grid(coin, current_price)
            self._save_config()
        
        # Auto-expansion si prix sort de la range
        if grid.auto_expand and current_price > grid.max_price:
            LOG.info(f"📈 Auto-expanding grid for {coin}")
            grid.max_price = current_price * 1.1
            self._expand_grid_up(coin, current_price)
            self._save_config()
        
        # Check for filled orders
        filled_orders = self._check_filled_orders(coin, current_price)
        
        for order in filled_orders:
            actions.append({
                "action": "order_filled",
                "order": asdict(order),
                "coin": coin,
                "price": current_price
            })
            
            # Create opposite order
            opposite = self._create_opposite_order(order, grid)
            if opposite:
                actions.append({
                    "action": "place_order",
                    "order": asdict(opposite),
                    "coin": coin
                })
        
        return actions
    
    def _check_filled_orders(self, coin: str, current_price: float) -> List[GridOrder]:
        """Vérifie les ordres remplis"""
        if coin not in self.orders:
            return []
        
        filled = []
        
        for order in self.orders[coin]:
            if order.status == "pending":
                # Buy order filled if price <= order price
                if order.side == "buy" and current_price <= order.price:
                    order.status = "filled"
                    order.filled_at = datetime.now().isoformat()
                    filled.append(order)
                    LOG.info(f"✅ Buy order filled: {coin} @ ${order.price:.2f}")
                
                # Sell order filled if price >= order price
                elif order.side == "sell" and current_price >= order.price:
                    order.status = "filled"
                    order.filled_at = datetime.now().isoformat()
                    
                    # Calculate profit
                    grid = self.grids[coin]
                    order.profit = order.quantity * order.price * (grid.profit_per_grid / 100)
                    
                    filled.append(order)
                    
                    # Update stats
                    self.stats[coin]["total_profits"] += order.profit
                    self.stats[coin]["total_trades"] += 1
                    self.stats[coin]["filled_sell_orders"] += 1
                    
                    LOG.info(f"✅ Sell order filled: {coin} @ ${order.price:.2f} | Profit: ${order.profit:.4f}")
        
        if filled:
            self._save_orders()
        
        return filled
    
    def _create_opposite_order(self, filled_order: GridOrder, grid: GridConfig) -> Optional[GridOrder]:
        """Crée l'ordre opposé après un fill"""
        if filled_order.side == "buy":
            # Create sell order above
            sell_price = filled_order.price * (1 + grid.profit_per_grid / 100)
            
            # Apply compounding if enabled
            quantity = filled_order.quantity
            if grid.compound_profit and filled_order.profit > 0:
                quantity *= 1.01  # Augmente légèrement la quantité
            
            return GridOrder(
                order_id=f"{filled_order.coin}_sell_{filled_order.grid_level}_new",
                coin=filled_order.coin,
                side="sell",
                price=sell_price,
                quantity=quantity,
                grid_level=filled_order.grid_level + 1,
                status="pending"
            )
        
        elif filled_order.side == "sell":
            # Create buy order below
            buy_price = filled_order.price * (1 - grid.profit_per_grid / 100)
            
            return GridOrder(
                order_id=f"{filled_order.coin}_buy_{filled_order.grid_level}_new",
                coin=filled_order.coin,
                side="buy",
                price=buy_price,
                quantity=filled_order.quantity,
                grid_level=filled_order.grid_level - 1,
                status="pending"
            )
        
        return None
    
    def _rebalance_grid(self, coin: str, current_price: float):
        """Rebalance la grille après trailing"""
        grid = self.grids[coin]
        
        # Recalculate grid levels
        new_prices = self._calculate_grid_levels(
            grid.min_price,
            grid.max_price,
            grid.grid_count,
            grid.mode
        )
        
        # Cancel pending orders outside new range
        if coin in self.orders:
            for order in self.orders[coin]:
                if order.status == "pending":
                    if order.price < grid.min_price or order.price > grid.max_price:
                        order.status = "cancelled"
        
        # Create new orders in the new range
        self._initialize_grid_orders(coin, current_price)
    
    def _expand_grid_up(self, coin: str, current_price: float):
        """Expand la grille vers le haut"""
        grid = self.grids[coin]
        
        # Add new sell orders above current max
        new_prices = self._calculate_grid_levels(
            grid.max_price,
            current_price * 1.1,
            5,  # Add 5 new levels
            grid.mode
        )
        
        quantity_per_order = grid.investment / (grid.grid_count * current_price)
        
        if coin not in self.orders:
            self.orders[coin] = []
        
        for i, price in enumerate(new_prices[1:]):  # Skip first (= old max)
            self.orders[coin].append(GridOrder(
                order_id=f"{coin}_sell_exp_{i}",
                coin=coin,
                side="sell",
                price=price,
                quantity=quantity_per_order,
                grid_level=grid.grid_count + i,
                status="pending"
            ))
        
        LOG.info(f"✅ Added {len(new_prices)-1} new sell orders for {coin}")
    
    def stop_grid(self, coin: str) -> bool:
        """Arrête une grille"""
        if coin not in self.grids:
            return False
        
        self.grids[coin].enabled = False
        
        # Cancel all pending orders
        if coin in self.orders:
            for order in self.orders[coin]:
                if order.status == "pending":
                    order.status = "cancelled"
        
        self._save_config()
        self._save_orders()
        
        LOG.info(f"⏹️ Stopped grid for {coin}")
        return True
    
    def delete_grid(self, coin: str) -> bool:
        """Supprime une grille"""
        if coin not in self.grids:
            return False
        
        del self.grids[coin]
        if coin in self.orders:
            del self.orders[coin]
        if coin in self.stats:
            del self.stats[coin]
        
        self._save_config()
        self._save_orders()
        
        LOG.info(f"🗑️ Deleted grid for {coin}")
        return True
    
    def get_grid_status(self, coin: str) -> Optional[Dict]:
        """Récupère le status d'une grille"""
        if coin not in self.grids:
            return None
        
        grid = self.grids[coin]
        orders = self.orders.get(coin, [])
        stats = self.stats.get(coin, {})
        
        pending_buy = [o for o in orders if o.status == "pending" and o.side == "buy"]
        pending_sell = [o for o in orders if o.status == "pending" and o.side == "sell"]
        filled = [o for o in orders if o.status == "filled"]
        
        return {
            "coin": coin,
            "enabled": grid.enabled,
            "mode": grid.mode.value,
            "price_range": {
                "min": grid.min_price,
                "max": grid.max_price
            },
            "grid_count": grid.grid_count,
            "profit_per_grid": grid.profit_per_grid,
            "investment": grid.investment,
            "orders": {
                "total": len(orders),
                "pending_buy": len(pending_buy),
                "pending_sell": len(pending_sell),
                "filled": len(filled)
            },
            "stats": stats
        }
    
    def get_all_grids(self) -> Dict[str, Dict]:
        """Récupère le status de toutes les grilles"""
        return {coin: self.get_grid_status(coin) for coin in self.grids.keys()}
    
    def get_total_stats(self) -> Dict:
        """Statistiques globales"""
        total_profits = sum(s.get("total_profits", 0) for s in self.stats.values())
        total_trades = sum(s.get("total_trades", 0) for s in self.stats.values())
        
        return {
            "active_grids": len([g for g in self.grids.values() if g.enabled]),
            "total_grids": len(self.grids),
            "total_profits": total_profits,
            "total_trades": total_trades,
            "avg_profit_per_trade": total_profits / total_trades if total_trades > 0 else 0
        }


# Singleton
_grid_engine = None

def get_grid_engine() -> GridInfinityEngine:
    """Get singleton instance"""
    global _grid_engine
    if _grid_engine is None:
        _grid_engine = GridInfinityEngine()
    return _grid_engine


if __name__ == "__main__":
    # Test
    print("🔥 Testing Grid Infinity Engine...")
    
    engine = GridInfinityEngine()
    
    # Create grid
    print("\n✅ Creating grid for BTC...")
    engine.create_grid("BTC", current_price=50000, investment=1000, grid_count=20, profit_per_grid=1.0)
    
    # Get status
    status = engine.get_grid_status("BTC")
    print(f"\n📊 Grid Status: {json.dumps(status, indent=2)}")
    
    # Simulate price updates
    print("\n🔄 Simulating price updates...")
    actions = engine.update_price("BTC", 49500)
    print(f"Actions: {len(actions)}")
    
    # Get stats
    stats = engine.get_total_stats()
    print(f"\n📈 Stats: {json.dumps(stats, indent=2)}")
    
    print("\n✅ Grid Infinity Engine test complete!")
