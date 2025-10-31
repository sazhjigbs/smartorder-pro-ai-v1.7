"""
Fee Optimizer
Optimise les frais via batching et timing optimal des transactions
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class FeeStrategy(Enum):
    AGGRESSIVE = "aggressive"  # Execute immédiatement
    BALANCED = "balanced"  # Balance entre vitesse et coût
    CONSERVATIVE = "conservative"  # Minimise coûts


@dataclass
class PendingOrder:
    """Ordre en attente d'optimisation"""
    symbol: str
    side: str
    quantity: float
    urgency: str  # "low", "medium", "high"
    created_at: float
    max_delay: float = 3600  # 1h max


class FeeOptimizer:
    """Optimiseur de frais de trading"""
    
    def __init__(self, strategy: FeeStrategy = FeeStrategy.BALANCED):
        self.strategy = strategy
        self.pending_orders: List[PendingOrder] = []
        self.executed_orders: List[Dict] = []
        self.total_fees_saved = 0.0
        
        # Frais par exchange (exemple)
        self.fee_tiers = {
            "maker": 0.001,  # 0.1%
            "taker": 0.002   # 0.2%
        }
    
    def add_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        urgency: str = "medium"
    ) -> str:
        """Ajoute un ordre à optimiser"""
        order = PendingOrder(
            symbol=symbol,
            side=side,
            quantity=quantity,
            urgency=urgency,
            created_at=time.time()
        )
        
        self.pending_orders.append(order)
        
        # Vérifier si on peut batcher
        if len(self.pending_orders) >= self._get_batch_threshold():
            self._execute_batch()
        
        return f"Order added to optimization queue ({len(self.pending_orders)} pending)"
    
    def _get_batch_threshold(self) -> int:
        """Seuil de batching selon stratégie"""
        thresholds = {
            FeeStrategy.AGGRESSIVE: 1,  # Pas de batching
            FeeStrategy.BALANCED: 5,    # Batch de 5
            FeeStrategy.CONSERVATIVE: 10  # Batch de 10
        }
        return thresholds.get(self.strategy, 5)
    
    def _execute_batch(self):
        """Exécute un batch d'ordres optimisé"""
        if not self.pending_orders:
            return
        
        # Grouper par symbole
        by_symbol = {}
        for order in self.pending_orders:
            if order.symbol not in by_symbol:
                by_symbol[order.symbol] = {"buy": [], "sell": []}
            by_symbol[order.symbol][order.side].append(order)
        
        # Exécuter chaque groupe
        for symbol, sides in by_symbol.items():
            # Netting: compenser buy et sell
            buy_qty = sum(o.quantity for o in sides["buy"])
            sell_qty = sum(o.quantity for o in sides["sell"])
            
            net_qty = buy_qty - sell_qty
            
            if net_qty > 0:
                # Net buy
                self._execute_optimized(symbol, "buy", net_qty, sides["buy"])
            elif net_qty < 0:
                # Net sell
                self._execute_optimized(symbol, "sell", abs(net_qty), sides["sell"])
            else:
                # Parfait netting - aucun ordre nécessaire!
                print(f"✅ Perfect netting for {symbol}: Zero net order!")
                fees_saved = (buy_qty + sell_qty) * self.fee_tiers["taker"]
                self.total_fees_saved += fees_saved
        
        # Vider la queue
        self.pending_orders.clear()
    
    def _execute_optimized(
        self,
        symbol: str,
        side: str,
        quantity: float,
        original_orders: List[PendingOrder]
    ):
        """Exécute un ordre optimisé"""
        
        # Timing optimal: utiliser maker order si possible
        use_maker = self._should_use_maker(original_orders)
        
        fee_type = "maker" if use_maker else "taker"
        fee_rate = self.fee_tiers[fee_type]
        fee = quantity * fee_rate
        
        # Calcul des frais économisés
        original_fee = sum(
            o.quantity * self.fee_tiers["taker"]
            for o in original_orders
        )
        saved = original_fee - fee
        self.total_fees_saved += saved
        
        execution = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "fee_type": fee_type,
            "fee": fee,
            "original_orders": len(original_orders),
            "fees_saved": saved,
            "savings_percent": (saved / original_fee * 100) if original_fee > 0 else 0,
            "timestamp": time.time()
        }
        
        self.executed_orders.append(execution)
        
        print(f"💰 Batch executed: {symbol} {side} {quantity:.4f}")
        print(f"   Fees saved: ${saved:.4f} ({execution['savings_percent']:.1f}%)")
    
    def _should_use_maker(self, orders: List[PendingOrder]) -> bool:
        """Détermine si on peut utiliser maker order"""
        # Si tous urgency = low, on peut attendre pour maker
        if all(o.urgency == "low" for o in orders):
            return True
        
        # Si stratégie conservative, favoriser maker
        if self.strategy == FeeStrategy.CONSERVATIVE:
            return sum(1 for o in orders if o.urgency != "high") / len(orders) > 0.5
        
        return False
    
    def optimize_timing(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Analyse le meilleur timing pour exécuter l'ordre
        
        Facteurs:
        - Volume du marché
        - Spread
        - Frais
        - Urgence
        """
        current_time = time.time()
        hour = int((current_time % 86400) / 3600)  # Heure du jour
        
        # Heures de faible volume (souvent moins de frais/spread)
        low_volume_hours = [2, 3, 4, 5, 6]  # 2h-6h UTC
        
        # Scoring du timing
        timing_score = 100.0
        
        if hour in low_volume_hours:
            timing_score -= 20  # Moins bon timing (faible liquidité)
        
        # Recommandation
        if timing_score >= 80:
            recommendation = "EXECUTE_NOW"
            delay_minutes = 0
        elif timing_score >= 60:
            recommendation = "EXECUTE_WITHIN_30MIN"
            delay_minutes = 30
        else:
            recommendation = "WAIT_FOR_BETTER_TIMING"
            # Calculer temps jusqu'à meilleure heure
            next_good_hour = (hour + 4) % 24
            delay_minutes = (next_good_hour - hour) * 60
        
        return {
            "symbol": symbol,
            "current_timing_score": timing_score,
            "recommendation": recommendation,
            "estimated_delay_minutes": delay_minutes,
            "estimated_fee_saving": self._estimate_savings(delay_minutes)
        }
    
    def _estimate_savings(self, delay_minutes: int) -> float:
        """Estime l'économie de frais si on attend"""
        # Simplification: 0.01% économie par heure d'attente
        return (delay_minutes / 60) * 0.01
    
    def batch_similar_orders(self, orders: List[Dict]) -> List[Dict]:
        """
        Batch des ordres similaires pour réduire frais
        
        Args:
            orders: Liste d'ordres [{symbol, side, quantity}]
        
        Returns:
            Liste d'ordres batchés
        """
        if not orders:
            return []
        
        # Grouper par (symbol, side)
        groups = {}
        for order in orders:
            key = (order["symbol"], order["side"])
            if key not in groups:
                groups[key] = []
            groups[key].append(order)
        
        # Créer ordres batchés
        batched = []
        for (symbol, side), order_group in groups.items():
            total_qty = sum(o["quantity"] for o in order_group)
            
            batched.append({
                "symbol": symbol,
                "side": side,
                "quantity": total_qty,
                "original_count": len(order_group),
                "fee_savings": len(order_group) - 1  # Économie de N-1 ordres
            })
        
        return batched
    
    def get_statistics(self) -> Dict:
        """Statistiques de l'optimisation"""
        if not self.executed_orders:
            return {
                "total_executed": 0,
                "total_fees_saved": 0,
                "avg_savings_percent": 0
            }
        
        total_saved = sum(e["fees_saved"] for e in self.executed_orders)
        avg_savings = sum(e["savings_percent"] for e in self.executed_orders) / len(self.executed_orders)
        
        maker_count = sum(1 for e in self.executed_orders if e["fee_type"] == "maker")
        
        return {
            "strategy": self.strategy.value,
            "total_executed": len(self.executed_orders),
            "pending_orders": len(self.pending_orders),
            "total_fees_saved": total_saved,
            "avg_savings_percent": avg_savings,
            "maker_orders": maker_count,
            "taker_orders": len(self.executed_orders) - maker_count,
            "maker_ratio": (maker_count / len(self.executed_orders) * 100) if self.executed_orders else 0
        }
    
    def force_execute_pending(self):
        """Force l'exécution de tous les ordres en attente"""
        if self.pending_orders:
            print(f"⚡ Force executing {len(self.pending_orders)} pending orders")
            self._execute_batch()


# Exemple d'utilisation
if __name__ == "__main__":
    optimizer = FeeOptimizer(strategy=FeeStrategy.BALANCED)
    
    # Ajouter plusieurs ordres
    print("=== Adding Orders ===")
    optimizer.add_order("BTCUSDT", "buy", 0.1, urgency="low")
    optimizer.add_order("BTCUSDT", "sell", 0.05, urgency="low")
    optimizer.add_order("ETHUSDT", "buy", 1.0, urgency="medium")
    optimizer.add_order("BTCUSDT", "buy", 0.15, urgency="low")
    optimizer.add_order("BTCUSDT", "sell", 0.2, urgency="low")
    
    # Forcer exécution
    print("\n=== Executing Batch ===")
    optimizer.force_execute_pending()
    
    # Stats
    print("\n📊 Optimization Stats:")
    stats = optimizer.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n💰 Total fees saved: ${stats['total_fees_saved']:.4f}")
    
    # Timing optimization
    print("\n=== Timing Analysis ===")
    timing = optimizer.optimize_timing("BTCUSDT", "buy", 1.0)
    print(f"Recommendation: {timing['recommendation']}")
    print(f"Estimated savings: {timing['estimated_fee_saving']:.2%}")
