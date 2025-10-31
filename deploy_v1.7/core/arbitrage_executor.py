"""
Arbitrage Executor
Exécute automatiquement les opportunités d'arbitrage cross-exchange
"""
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ArbitrageType(Enum):
    SIMPLE = "simple"  # Acheter sur A, vendre sur B
    TRIANGULAR = "triangular"  # A->B->C->A
    STATISTICAL = "statistical"  # Basé sur corrélations


@dataclass
class ArbitrageOpportunity:
    """Opportunité d'arbitrage"""
    type: ArbitrageType
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_percent: float
    estimated_profit: float
    min_quantity: float
    max_quantity: float
    timestamp: float
    
    @property
    def is_profitable(self) -> bool:
        return self.estimated_profit > 0 and self.spread_percent > 0.5


class ArbitrageExecutor:
    """Exécuteur d'arbitrage automatique"""
    
    def __init__(self, min_profit_percent: float = 0.5):
        self.min_profit_percent = min_profit_percent
        self.active_arbitrages: List[Dict] = []
        self.executed_arbitrages: List[Dict] = []
        self.exchange_clients = {}
        
    def register_exchange_client(self, exchange_name: str, client):
        """Enregistre un client d'exchange"""
        self.exchange_clients[exchange_name] = client
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> Dict:
        """
        Exécute une opportunité d'arbitrage
        
        Steps:
        1. Vérifier balances
        2. Acheter sur exchange A
        3. Vendre sur exchange B
        4. Calculer profit réel
        """
        if not opportunity.is_profitable:
            return {"success": False, "reason": "Not profitable"}
        
        if opportunity.spread_percent < self.min_profit_percent:
            return {"success": False, "reason": "Spread too low"}
        
        # Vérifier si exchanges sont disponibles
        if opportunity.buy_exchange not in self.exchange_clients:
            return {"success": False, "reason": f"Exchange {opportunity.buy_exchange} not available"}
        
        if opportunity.sell_exchange not in self.exchange_clients:
            return {"success": False, "reason": f"Exchange {opportunity.sell_exchange} not available"}
        
        execution_id = f"ARB_{int(time.time()*1000)}"
        
        try:
            # Étape 1: Calculer quantité optimale
            quantity = self._calculate_optimal_quantity(opportunity)
            
            # Étape 2: Placer ordre d'achat
            buy_client = self.exchange_clients[opportunity.buy_exchange]
            buy_order = await self._place_buy_order(
                buy_client,
                opportunity.symbol,
                quantity,
                opportunity.buy_price
            )
            
            if not buy_order["success"]:
                return {
                    "success": False,
                    "reason": "Buy order failed",
                    "details": buy_order
                }
            
            # Étape 3: Placer ordre de vente
            sell_client = self.exchange_clients[opportunity.sell_exchange]
            sell_order = await self._place_sell_order(
                sell_client,
                opportunity.symbol,
                quantity,
                opportunity.sell_price
            )
            
            if not sell_order["success"]:
                # Annuler l'ordre d'achat si vente échoue
                await self._cancel_order(buy_client, buy_order["order_id"])
                return {
                    "success": False,
                    "reason": "Sell order failed",
                    "details": sell_order
                }
            
            # Étape 4: Calculer profit réel
            buy_cost = buy_order["filled_price"] * quantity + buy_order["fee"]
            sell_revenue = sell_order["filled_price"] * quantity - sell_order["fee"]
            profit = sell_revenue - buy_cost
            profit_percent = (profit / buy_cost) * 100
            
            result = {
                "success": True,
                "execution_id": execution_id,
                "symbol": opportunity.symbol,
                "quantity": quantity,
                "buy_exchange": opportunity.buy_exchange,
                "sell_exchange": opportunity.sell_exchange,
                "buy_price": buy_order["filled_price"],
                "sell_price": sell_order["filled_price"],
                "buy_cost": buy_cost,
                "sell_revenue": sell_revenue,
                "profit": profit,
                "profit_percent": profit_percent,
                "estimated_profit": opportunity.estimated_profit,
                "timestamp": time.time()
            }
            
            self.executed_arbitrages.append(result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "reason": "Execution error",
                "error": str(e)
            }
    
    async def _place_buy_order(self, client, symbol: str, quantity: float, price: float) -> Dict:
        """Place un ordre d'achat"""
        # Simulation (remplacer par vrai appel API)
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "order_id": f"BUY_{int(time.time()*1000)}",
            "filled_price": price * 1.0001,  # Simule légère variation
            "fee": quantity * price * 0.001  # 0.1% fee
        }
    
    async def _place_sell_order(self, client, symbol: str, quantity: float, price: float) -> Dict:
        """Place un ordre de vente"""
        # Simulation (remplacer par vrai appel API)
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "order_id": f"SELL_{int(time.time()*1000)}",
            "filled_price": price * 0.9999,  # Simule légère variation
            "fee": quantity * price * 0.001  # 0.1% fee
        }
    
    async def _cancel_order(self, client, order_id: str):
        """Annule un ordre"""
        # Simulation
        await asyncio.sleep(0.05)
        return {"success": True}
    
    def _calculate_optimal_quantity(self, opportunity: ArbitrageOpportunity) -> float:
        """Calcule la quantité optimale pour l'arbitrage"""
        # Prendre en compte:
        # 1. Liquidité disponible
        # 2. Capital disponible
        # 3. Limites d'exposition
        
        # Pour simplification, prendre 50% du max
        return opportunity.max_quantity * 0.5
    
    async def scan_and_execute(self, opportunities: List[ArbitrageOpportunity]) -> List[Dict]:
        """Scanne et exécute les meilleures opportunités"""
        results = []
        
        # Filtrer les opportunités profitables
        profitable = [
            opp for opp in opportunities
            if opp.is_profitable and opp.spread_percent >= self.min_profit_percent
        ]
        
        # Trier par profit estimé
        profitable.sort(key=lambda x: x.estimated_profit, reverse=True)
        
        # Exécuter les meilleures (max 3 simultanément)
        for opp in profitable[:3]:
            result = await self.execute_arbitrage(opp)
            results.append(result)
            
            if result["success"]:
                print(f"✅ Arbitrage executed: {opp.symbol} - Profit: ${result['profit']:.2f}")
            else:
                print(f"❌ Arbitrage failed: {opp.symbol} - {result['reason']}")
        
        return results
    
    def get_statistics(self) -> Dict:
        """Statistiques des arbitrages"""
        if not self.executed_arbitrages:
            return {
                "total_executed": 0,
                "total_profit": 0,
                "avg_profit": 0,
                "success_rate": 0
            }
        
        successful = [a for a in self.executed_arbitrages if a["success"]]
        total_profit = sum(a.get("profit", 0) for a in successful)
        
        return {
            "total_executed": len(self.executed_arbitrages),
            "successful": len(successful),
            "failed": len(self.executed_arbitrages) - len(successful),
            "success_rate": len(successful) / len(self.executed_arbitrages) * 100,
            "total_profit": total_profit,
            "avg_profit": total_profit / len(successful) if successful else 0,
            "avg_profit_percent": sum(a.get("profit_percent", 0) for a in successful) / len(successful) if successful else 0
        }
    
    def get_best_opportunities(self, limit: int = 10) -> List[Dict]:
        """Retourne les meilleures opportunités récentes"""
        sorted_arbs = sorted(
            self.executed_arbitrages,
            key=lambda x: x.get("profit", 0),
            reverse=True
        )
        return sorted_arbs[:limit]


# Exemple d'utilisation
async def main():
    executor = ArbitrageExecutor(min_profit_percent=0.5)
    
    # Simuler des clients (remplacer par vrais clients)
    executor.register_exchange_client("binance", {"name": "binance"})
    executor.register_exchange_client("bybit", {"name": "bybit"})
    
    # Opportunité d'arbitrage
    opportunity = ArbitrageOpportunity(
        type=ArbitrageType.SIMPLE,
        symbol="BTCUSDT",
        buy_exchange="binance",
        sell_exchange="bybit",
        buy_price=50000,
        sell_price=50400,
        spread_percent=0.8,
        estimated_profit=40.0,
        min_quantity=0.001,
        max_quantity=0.1,
        timestamp=time.time()
    )
    
    # Exécuter
    result = await executor.execute_arbitrage(opportunity)
    print(f"\n✅ Result: {result}")
    
    # Stats
    print(f"\n📊 Stats: {executor.get_statistics()}")


if __name__ == "__main__":
    asyncio.run(main())
