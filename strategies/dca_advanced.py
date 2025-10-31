#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - DCA Advanced Strategy
==========================================
DCA Intelligent style 3Commas avec safety orders
by MAIGA ABOUBACAR

Features:
- Safety orders avec martingale (1x, 2x, 4x, 8x)
- Trailing take-profit
- Volume-based sizing
- Deviation-based entries
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

LOG = logging.getLogger("dca_advanced")
LOG.setLevel(logging.INFO)

@dataclass
class DCAOrder:
    order_id: str
    order_num: int  # 0 = base, 1+ = safety orders
    price: float
    quantity: float
    filled: bool = False
    filled_at: Optional[str] = None

@dataclass
class DCAPosition:
    coin: str
    base_order: DCAOrder
    safety_orders: List[DCAOrder]
    avg_entry_price: float
    total_invested: float
    target_profit_price: float
    trailing_active: bool = False
    highest_price: float = 0.0

class DCAAdvancedStrategy:
    """
    DCA Strategy avancée style 3Commas
    
    Configuration:
    - Base order: Premier achat
    - Safety orders: 1x, 2x, 4x, 8x (martingale)
    - Price deviation: -2.5%, -5%, -7.5%, -10%
    - Take profit: +3%
    - Trailing: actif si +3%
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.positions: Dict[str, DCAPosition] = {}
        LOG.info("✅ DCA Advanced Strategy initialized")
    
    def _default_config(self) -> Dict:
        return {
            "base_order_usd": 100,
            "safety_order_usd": 100,
            "safety_order_count": 4,
            "safety_order_multiplier": 2.0,  # 1x, 2x, 4x, 8x
            "price_deviation_percent": 2.5,  # -2.5% par safety order
            "take_profit_percent": 3.0,
            "trailing_enabled": True,
            "trailing_deviation": 1.0,  # -1% from peak
            "volume_based_sizing": True
        }
    
    def create_position(self, coin: str, current_price: float) -> DCAPosition:
        """Crée une nouvelle position DCA"""
        if coin in self.positions:
            LOG.warning(f"⚠️ Position already exists for {coin}")
            return self.positions[coin]
        
        # Base order
        base_quantity = self.config["base_order_usd"] / current_price
        base_order = DCAOrder(
            order_id=f"{coin}_base_0",
            order_num=0,
            price=current_price,
            quantity=base_quantity,
            filled=True,
            filled_at=datetime.now().isoformat()
        )
        
        # Safety orders
        safety_orders = []
        base_so_usd = self.config["safety_order_usd"]
        multiplier = self.config["safety_order_multiplier"]
        deviation = self.config["price_deviation_percent"]
        
        for i in range(1, self.config["safety_order_count"] + 1):
            # Martingale sizing: 1x, 2x, 4x, 8x
            so_size = base_so_usd * (multiplier ** (i - 1))
            
            # Price deviation: -2.5%, -5%, -7.5%, -10%
            so_price = current_price * (1 - (deviation * i) / 100)
            so_quantity = so_size / so_price
            
            safety_orders.append(DCAOrder(
                order_id=f"{coin}_so_{i}",
                order_num=i,
                price=so_price,
                quantity=so_quantity,
                filled=False
            ))
        
        # Calculate targets
        total_invested = self.config["base_order_usd"]
        avg_entry = current_price
        target_profit_price = current_price * (1 + self.config["take_profit_percent"] / 100)
        
        position = DCAPosition(
            coin=coin,
            base_order=base_order,
            safety_orders=safety_orders,
            avg_entry_price=avg_entry,
            total_invested=total_invested,
            target_profit_price=target_profit_price,
            trailing_active=False,
            highest_price=current_price
        )
        
        self.positions[coin] = position
        
        LOG.info(f"✅ Created DCA position for {coin}")
        LOG.info(f"   Base: ${current_price:.2f} x {base_quantity:.6f}")
        LOG.info(f"   Safety orders: {len(safety_orders)}")
        LOG.info(f"   Target: ${target_profit_price:.2f} (+{self.config['take_profit_percent']}%)")
        
        return position
    
    def update_position(self, coin: str, current_price: float) -> Dict:
        """Met à jour position avec nouveau prix"""
        if coin not in self.positions:
            return {"action": "none"}
        
        position = self.positions[coin]
        actions = {"action": "none", "orders": []}
        
        # Check safety orders à remplir
        for so in position.safety_orders:
            if not so.filled and current_price <= so.price:
                so.filled = True
                so.filled_at = datetime.now().isoformat()
                
                # Recalculate avg entry
                position.total_invested += so.price * so.quantity
                total_quantity = position.base_order.quantity + sum(
                    s.quantity for s in position.safety_orders if s.filled
                )
                position.avg_entry_price = position.total_invested / total_quantity
                
                # Recalculate target
                position.target_profit_price = position.avg_entry_price * (
                    1 + self.config["take_profit_percent"] / 100
                )
                
                actions["orders"].append({
                    "type": "safety_order_filled",
                    "order": so.order_id,
                    "price": so.price,
                    "quantity": so.quantity,
                    "new_avg_entry": position.avg_entry_price,
                    "new_target": position.target_profit_price
                })
                
                LOG.info(f"✅ Safety order {so.order_num} filled: {coin} @ ${so.price:.2f}")
                LOG.info(f"   New avg entry: ${position.avg_entry_price:.2f}")
                LOG.info(f"   New target: ${position.target_profit_price:.2f}")
        
        # Update highest price for trailing
        if current_price > position.highest_price:
            position.highest_price = current_price
        
        # Check take profit
        if current_price >= position.target_profit_price:
            if self.config["trailing_enabled"]:
                # Activate trailing
                if not position.trailing_active:
                    position.trailing_active = True
                    LOG.info(f"✅ Trailing take-profit activated for {coin}")
                
                # Check trailing stop
                trailing_stop = position.highest_price * (
                    1 - self.config["trailing_deviation"] / 100
                )
                
                if current_price <= trailing_stop:
                    # Close position
                    profit_percent = ((current_price - position.avg_entry_price) / 
                                     position.avg_entry_price) * 100
                    
                    actions["action"] = "close_position"
                    actions["close_price"] = current_price
                    actions["profit_percent"] = profit_percent
                    
                    LOG.info(f"✅ Position closed (trailing): {coin}")
                    LOG.info(f"   Entry: ${position.avg_entry_price:.2f}")
                    LOG.info(f"   Exit: ${current_price:.2f}")
                    LOG.info(f"   Profit: {profit_percent:.2f}%")
                    
                    del self.positions[coin]
            else:
                # Close immédiatement au target
                profit_percent = ((current_price - position.avg_entry_price) / 
                                 position.avg_entry_price) * 100
                
                actions["action"] = "close_position"
                actions["close_price"] = current_price
                actions["profit_percent"] = profit_percent
                
                LOG.info(f"✅ Position closed (target): {coin}")
                LOG.info(f"   Profit: {profit_percent:.2f}%")
                
                del self.positions[coin]
        
        return actions
    
    def get_position_status(self, coin: str) -> Optional[Dict]:
        """Récupère status d'une position"""
        if coin not in self.positions:
            return None
        
        position = self.positions[coin]
        
        filled_sos = [so for so in position.safety_orders if so.filled]
        pending_sos = [so for so in position.safety_orders if not so.filled]
        
        return {
            "coin": coin,
            "avg_entry_price": position.avg_entry_price,
            "total_invested": position.total_invested,
            "target_profit_price": position.target_profit_price,
            "trailing_active": position.trailing_active,
            "highest_price": position.highest_price,
            "safety_orders": {
                "filled": len(filled_sos),
                "pending": len(pending_sos),
                "total": len(position.safety_orders)
            }
        }
    
    def close_position(self, coin: str, current_price: float, reason: str = "manual") -> Dict:
        """Ferme une position manuellement"""
        if coin not in self.positions:
            return {"success": False, "error": "Position not found"}
        
        position = self.positions[coin]
        profit_percent = ((current_price - position.avg_entry_price) / 
                         position.avg_entry_price) * 100
        
        result = {
            "success": True,
            "coin": coin,
            "entry_price": position.avg_entry_price,
            "exit_price": current_price,
            "profit_percent": profit_percent,
            "total_invested": position.total_invested,
            "reason": reason
        }
        
        del self.positions[coin]
        LOG.info(f"✅ Position closed ({reason}): {coin} | Profit: {profit_percent:.2f}%")
        
        return result


_dca_strategy = None

def get_dca_strategy():
    global _dca_strategy
    if _dca_strategy is None:
        _dca_strategy = DCAAdvancedStrategy()
    return _dca_strategy


if __name__ == "__main__":
    # Test
    print("🔥 Testing DCA Advanced Strategy...")
    
    dca = DCAAdvancedStrategy()
    
    # Create position
    print("\n✅ Creating DCA position for BTC...")
    position = dca.create_position("BTC", current_price=50000)
    
    # Simulate price drops (trigger safety orders)
    print("\n📉 Simulating price drops...")
    dca.update_position("BTC", 48750)  # SO1: -2.5%
    dca.update_position("BTC", 47500)  # SO2: -5%
    
    # Simulate price recovery
    print("\n📈 Simulating price recovery...")
    dca.update_position("BTC", 49000)
    result = dca.update_position("BTC", 50500)  # Above target
    
    if result["action"] == "close_position":
        print(f"\n✅ Position closed with {result['profit_percent']:.2f}% profit")
    
    print("\n✅ DCA Advanced Strategy test complete!")
