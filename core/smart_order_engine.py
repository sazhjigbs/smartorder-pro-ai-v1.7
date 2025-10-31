"""
Smart Order Engine - Types d'ordres avancés
OCO (One-Cancels-Other), Iceberg, TWAP, Bracket Orders
"""
import time
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random


class OrderType(Enum):
    OCO = "oco"  # One-Cancels-Other
    ICEBERG = "iceberg"  # Ordre caché
    TWAP = "twap"  # Time-Weighted Average Price
    BRACKET = "bracket"  # Stop + Target simultané
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"
    PARTIALLY_FILLED = "partially_filled"


@dataclass
class SmartOrder:
    """Ordre intelligent"""
    order_id: str
    order_type: OrderType
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    status: OrderStatus = OrderStatus.PENDING
    
    # Prix
    price: Optional[float] = None
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    
    # Spécifique Iceberg
    visible_quantity: Optional[float] = None
    filled_quantity: float = 0.0
    
    # Spécifique TWAP
    duration_seconds: Optional[int] = None
    num_slices: Optional[int] = None
    slice_interval: Optional[int] = None
    
    # Métadonnées
    created_at: float = 0.0
    filled_at: Optional[float] = None
    avg_fill_price: Optional[float] = None
    
    # Callback
    on_fill: Optional[Callable] = None
    on_cancel: Optional[Callable] = None


class SmartOrderEngine:
    """Moteur d'ordres intelligents"""
    
    def __init__(self):
        self.orders: Dict[str, SmartOrder] = {}
        self.oco_groups: Dict[str, List[str]] = {}  # group_id -> [order_ids]
        self.execution_log: List[Dict] = []
        
    async def place_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss_price: float,
        take_profit_price: float
    ) -> Dict:
        """
        Place un ordre OCO (One-Cancels-Other)
        Si le stop loss est touché, le take profit est annulé et vice-versa
        """
        group_id = f"OCO_{symbol}_{int(time.time()*1000)}"
        
        # Ordre Stop Loss
        stop_order = SmartOrder(
            order_id=f"{group_id}_STOP",
            order_type=OrderType.OCO,
            symbol=symbol,
            side="sell" if side == "buy" else "buy",
            quantity=quantity,
            stop_price=stop_loss_price,
            status=OrderStatus.ACTIVE,
            created_at=time.time()
        )
        
        # Ordre Take Profit
        profit_order = SmartOrder(
            order_id=f"{group_id}_PROFIT",
            order_type=OrderType.OCO,
            symbol=symbol,
            side="sell" if side == "buy" else "buy",
            quantity=quantity,
            target_price=take_profit_price,
            status=OrderStatus.ACTIVE,
            created_at=time.time()
        )
        
        self.orders[stop_order.order_id] = stop_order
        self.orders[profit_order.order_id] = profit_order
        self.oco_groups[group_id] = [stop_order.order_id, profit_order.order_id]
        
        return {
            "group_id": group_id,
            "stop_order_id": stop_order.order_id,
            "profit_order_id": profit_order.order_id,
            "status": "active"
        }
    
    async def place_iceberg_order(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        visible_quantity: float,
        price: Optional[float] = None
    ) -> str:
        """
        Place un ordre Iceberg (masque la quantité totale)
        Seule une partie visible est affichée au marché
        """
        order = SmartOrder(
            order_id=f"ICEBERG_{symbol}_{int(time.time()*1000)}",
            order_type=OrderType.ICEBERG,
            symbol=symbol,
            side=side,
            quantity=total_quantity,
            visible_quantity=visible_quantity,
            price=price,
            status=OrderStatus.ACTIVE,
            created_at=time.time()
        )
        
        self.orders[order.order_id] = order
        
        # Simulation d'exécution progressive
        asyncio.create_task(self._execute_iceberg_slices(order))
        
        return order.order_id
    
    async def place_twap_order(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        duration_seconds: int,
        num_slices: int = 10
    ) -> str:
        """
        Place un ordre TWAP (Time-Weighted Average Price)
        Divise l'ordre en plusieurs tranches sur une durée
        """
        order = SmartOrder(
            order_id=f"TWAP_{symbol}_{int(time.time()*1000)}",
            order_type=OrderType.TWAP,
            symbol=symbol,
            side=side,
            quantity=total_quantity,
            duration_seconds=duration_seconds,
            num_slices=num_slices,
            slice_interval=duration_seconds // num_slices,
            status=OrderStatus.ACTIVE,
            created_at=time.time()
        )
        
        self.orders[order.order_id] = order
        
        # Exécution progressive
        asyncio.create_task(self._execute_twap_slices(order))
        
        return order.order_id
    
    async def place_bracket_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Dict:
        """
        Place un Bracket Order (Entry + Stop + Target)
        Combine entry, stop loss et take profit
        """
        bracket_id = f"BRACKET_{symbol}_{int(time.time()*1000)}"
        
        # Ordre d'entrée
        entry_order = SmartOrder(
            order_id=f"{bracket_id}_ENTRY",
            order_type=OrderType.BRACKET,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=entry_price,
            status=OrderStatus.ACTIVE,
            created_at=time.time()
        )
        
        self.orders[entry_order.order_id] = entry_order
        
        # Une fois l'entry rempli, créer OCO
        entry_order.on_fill = lambda: asyncio.create_task(
            self.place_oco_order(symbol, side, quantity, stop_loss, take_profit)
        )
        
        return {
            "bracket_id": bracket_id,
            "entry_order_id": entry_order.order_id,
            "status": "active"
        }
    
    async def _execute_iceberg_slices(self, order: SmartOrder):
        """Exécute progressivement un ordre Iceberg"""
        while order.filled_quantity < order.quantity:
            remaining = order.quantity - order.filled_quantity
            slice_qty = min(order.visible_quantity, remaining)
            
            # Simulation d'exécution (remplacer par vrai appel exchange)
            await asyncio.sleep(random.uniform(1, 3))
            
            order.filled_quantity += slice_qty
            
            self.execution_log.append({
                "order_id": order.order_id,
                "type": "iceberg_slice",
                "quantity": slice_qty,
                "filled_total": order.filled_quantity,
                "timestamp": time.time()
            })
            
            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
                order.filled_at = time.time()
                if order.on_fill:
                    order.on_fill()
                break
    
    async def _execute_twap_slices(self, order: SmartOrder):
        """Exécute progressivement un ordre TWAP"""
        slice_qty = order.quantity / order.num_slices
        
        for i in range(order.num_slices):
            # Attendre l'intervalle
            await asyncio.sleep(order.slice_interval)
            
            # Exécuter la tranche
            order.filled_quantity += slice_qty
            
            self.execution_log.append({
                "order_id": order.order_id,
                "type": "twap_slice",
                "slice_number": i + 1,
                "quantity": slice_qty,
                "filled_total": order.filled_quantity,
                "timestamp": time.time()
            })
            
            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
                order.filled_at = time.time()
                if order.on_fill:
                    order.on_fill()
                break
    
    def check_oco_trigger(self, group_id: str, current_price: float) -> Optional[str]:
        """Vérifie si un ordre OCO doit être déclenché"""
        if group_id not in self.oco_groups:
            return None
        
        order_ids = self.oco_groups[group_id]
        
        for order_id in order_ids:
            order = self.orders.get(order_id)
            if not order or order.status != OrderStatus.ACTIVE:
                continue
            
            triggered = False
            
            # Vérifier Stop Loss
            if order.stop_price:
                if (order.side == "sell" and current_price <= order.stop_price) or \
                   (order.side == "buy" and current_price >= order.stop_price):
                    triggered = True
            
            # Vérifier Take Profit
            if order.target_price:
                if (order.side == "sell" and current_price >= order.target_price) or \
                   (order.side == "buy" and current_price <= order.target_price):
                    triggered = True
            
            if triggered:
                # Remplir cet ordre
                order.status = OrderStatus.FILLED
                order.filled_at = time.time()
                order.avg_fill_price = current_price
                
                # Annuler l'autre ordre
                other_order_id = [oid for oid in order_ids if oid != order_id][0]
                other_order = self.orders[other_order_id]
                other_order.status = OrderStatus.CANCELLED
                
                if order.on_fill:
                    order.on_fill()
                
                return order_id
        
        return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Annule un ordre"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        order.status = OrderStatus.CANCELLED
        
        if order.on_cancel:
            order.on_cancel()
        
        return True
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Récupère le statut d'un ordre"""
        if order_id not in self.orders:
            return None
        
        order = self.orders[order_id]
        return {
            "order_id": order.order_id,
            "type": order.order_type.value,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "filled_quantity": order.filled_quantity,
            "status": order.status.value,
            "avg_fill_price": order.avg_fill_price
        }
    
    def get_active_orders(self) -> List[Dict]:
        """Liste tous les ordres actifs"""
        return [
            self.get_order_status(oid)
            for oid, order in self.orders.items()
            if order.status == OrderStatus.ACTIVE
        ]
    
    def get_statistics(self) -> Dict:
        """Statistiques des ordres"""
        total = len(self.orders)
        filled = sum(1 for o in self.orders.values() if o.status == OrderStatus.FILLED)
        cancelled = sum(1 for o in self.orders.values() if o.status == OrderStatus.CANCELLED)
        active = sum(1 for o in self.orders.values() if o.status == OrderStatus.ACTIVE)
        
        return {
            "total_orders": total,
            "filled": filled,
            "cancelled": cancelled,
            "active": active,
            "fill_rate": (filled / total * 100) if total > 0 else 0
        }


# Exemple d'utilisation
async def main():
    engine = SmartOrderEngine()
    
    print("=== Test OCO Order ===")
    oco_result = await engine.place_oco_order(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.1,
        stop_loss_price=49000,
        take_profit_price=52000
    )
    print(f"✅ OCO créé: {oco_result}")
    
    print("\n=== Test Iceberg Order ===")
    iceberg_id = await engine.place_iceberg_order(
        symbol="ETHUSDT",
        side="buy",
        total_quantity=10.0,
        visible_quantity=2.0,
        price=3000
    )
    print(f"✅ Iceberg créé: {iceberg_id}")
    
    print("\n=== Test TWAP Order ===")
    twap_id = await engine.place_twap_order(
        symbol="BTCUSDT",
        side="buy",
        total_quantity=1.0,
        duration_seconds=60,
        num_slices=6
    )
    print(f"✅ TWAP créé: {twap_id}")
    
    await asyncio.sleep(5)
    print("\n📊 Stats:", engine.get_statistics())
    print("📋 Active Orders:", len(engine.get_active_orders()))


if __name__ == "__main__":
    asyncio.run(main())
