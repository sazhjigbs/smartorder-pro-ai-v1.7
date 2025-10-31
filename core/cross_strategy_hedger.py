"""
Cross-Strategy Hedging
Combine Grid Trading + DCA + Futures pour hedging optimal
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class HedgingMode(Enum):
    CONSERVATIVE = "conservative"  # Hedge 100%
    MODERATE = "moderate"  # Hedge 50%
    AGGRESSIVE = "aggressive"  # Hedge 25%
    DYNAMIC = "dynamic"  # Ajuste selon volatilité


@dataclass
class HedgePosition:
    """Position de hedge"""
    strategy: str  # "grid", "dca", "futures"
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_pnl: float = 0.0
    active: bool = True


class CrossStrategyHedger:
    """
    Hedger multi-stratégies
    Protège le portfolio en combinant plusieurs stratégies
    """
    
    def __init__(self, mode: HedgingMode = HedgingMode.MODERATE):
        self.mode = mode
        self.spot_positions: List[HedgePosition] = []
        self.hedge_positions: List[HedgePosition] = []
        self.total_exposure = 0.0
        self.hedged_exposure = 0.0
    
    def add_spot_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float
    ) -> str:
        """Ajoute une position spot à hedger"""
        position = HedgePosition(
            strategy="spot",
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price
        )
        
        self.spot_positions.append(position)
        self.total_exposure += quantity * entry_price
        
        # Créer hedge automatiquement
        hedge_result = self._create_hedge(position)
        
        return f"Position added, hedge: {hedge_result['strategy']}"
    
    def _create_hedge(self, spot_position: HedgePosition) -> Dict:
        """
        Crée une stratégie de hedge optimale
        
        Stratégies disponibles:
        1. Grid Trading inversé
        2. DCA inversé (vendre progressivement)
        3. Futures short
        """
        symbol = spot_position.symbol
        quantity = spot_position.quantity
        
        # Calculer ratio de hedge selon mode
        hedge_ratio = self._get_hedge_ratio()
        hedge_quantity = quantity * hedge_ratio
        
        # Choisir stratégie selon conditions de marché
        volatility = self._estimate_volatility(symbol)
        
        if volatility > 0.05:  # Haute volatilité
            # Utiliser Futures pour hedge rapide
            hedge_strategy = self._open_futures_hedge(
                symbol,
                hedge_quantity,
                spot_position.entry_price
            )
            strategy_type = "futures"
        
        elif volatility > 0.02:  # Volatilité moyenne
            # Utiliser Grid Trading inversé
            hedge_strategy = self._open_grid_hedge(
                symbol,
                hedge_quantity,
                spot_position.entry_price
            )
            strategy_type = "grid"
        
        else:  # Basse volatilité
            # Utiliser DCA inversé
            hedge_strategy = self._open_dca_hedge(
                symbol,
                hedge_quantity,
                spot_position.entry_price
            )
            strategy_type = "dca"
        
        hedge_position = HedgePosition(
            strategy=strategy_type,
            symbol=symbol,
            side="sell" if spot_position.side == "buy" else "buy",
            quantity=hedge_quantity,
            entry_price=hedge_strategy["entry_price"]
        )
        
        self.hedge_positions.append(hedge_position)
        self.hedged_exposure += hedge_quantity * hedge_strategy["entry_price"]
        
        return {
            "strategy": strategy_type,
            "hedge_ratio": hedge_ratio,
            "hedge_quantity": hedge_quantity,
            "details": hedge_strategy
        }
    
    def _open_futures_hedge(self, symbol: str, quantity: float, spot_price: float) -> Dict:
        """Ouvre un hedge via Futures (short)"""
        # En pratique, ouvrir position short futures
        return {
            "type": "futures_short",
            "symbol": symbol,
            "quantity": quantity,
            "entry_price": spot_price * 1.0005,  # Légère prime
            "leverage": 3,
            "margin_required": (quantity * spot_price) / 3
        }
    
    def _open_grid_hedge(self, symbol: str, quantity: float, spot_price: float) -> Dict:
        """Ouvre un Grid Trading inversé"""
        # Grid qui vend progressivement au-dessus du prix spot
        num_levels = 10
        grid_spacing = 0.01  # 1%
        
        sell_levels = []
        for i in range(num_levels):
            level_price = spot_price * (1 + (i + 1) * grid_spacing)
            level_quantity = quantity / num_levels
            sell_levels.append({
                "price": level_price,
                "quantity": level_quantity
            })
        
        return {
            "type": "grid_sell",
            "symbol": symbol,
            "total_quantity": quantity,
            "entry_price": spot_price,
            "num_levels": num_levels,
            "levels": sell_levels
        }
    
    def _open_dca_hedge(self, symbol: str, quantity: float, spot_price: float) -> Dict:
        """Ouvre un DCA inversé (vente progressive)"""
        # Vendre par tranches si le prix monte
        num_tranches = 5
        tranche_size = quantity / num_tranches
        
        tranches = []
        for i in range(num_tranches):
            target_price = spot_price * (1 + (i + 1) * 0.02)  # +2% par tranche
            tranches.append({
                "price": target_price,
                "quantity": tranche_size
            })
        
        return {
            "type": "dca_sell",
            "symbol": symbol,
            "total_quantity": quantity,
            "entry_price": spot_price,
            "num_tranches": num_tranches,
            "tranches": tranches
        }
    
    def _get_hedge_ratio(self) -> float:
        """Retourne le ratio de hedge selon le mode"""
        ratios = {
            HedgingMode.CONSERVATIVE: 1.0,  # 100%
            HedgingMode.MODERATE: 0.5,      # 50%
            HedgingMode.AGGRESSIVE: 0.25,   # 25%
            HedgingMode.DYNAMIC: self._calculate_dynamic_ratio()
        }
        return ratios.get(self.mode, 0.5)
    
    def _calculate_dynamic_ratio(self) -> float:
        """Calcule ratio dynamique selon conditions"""
        # Basé sur volatilité, trend, etc.
        # Pour simplification: moyenne
        return 0.5
    
    def _estimate_volatility(self, symbol: str) -> float:
        """Estime la volatilité (simplifié)"""
        # En pratique, calculer ATR ou std des prix
        import random
        return random.uniform(0.01, 0.08)
    
    def update_positions(self, current_prices: Dict[str, float]) -> Dict:
        """Met à jour les PnL de toutes les positions"""
        total_spot_pnl = 0.0
        total_hedge_pnl = 0.0
        
        # PnL positions spot
        for pos in self.spot_positions:
            if not pos.active:
                continue
            
            current_price = current_prices.get(pos.symbol, pos.entry_price)
            
            if pos.side == "buy":
                pnl = (current_price - pos.entry_price) * pos.quantity
            else:
                pnl = (pos.entry_price - current_price) * pos.quantity
            
            pos.current_pnl = pnl
            total_spot_pnl += pnl
        
        # PnL positions hedge
        for pos in self.hedge_positions:
            if not pos.active:
                continue
            
            current_price = current_prices.get(pos.symbol, pos.entry_price)
            
            if pos.side == "sell":
                pnl = (pos.entry_price - current_price) * pos.quantity
            else:
                pnl = (current_price - pos.entry_price) * pos.quantity
            
            pos.current_pnl = pnl
            total_hedge_pnl += pnl
        
        # PnL net
        net_pnl = total_spot_pnl + total_hedge_pnl
        
        # Efficacité du hedge
        if total_spot_pnl < 0:
            hedge_efficiency = abs(total_hedge_pnl / total_spot_pnl) * 100 if total_spot_pnl != 0 else 0
        else:
            hedge_efficiency = 100  # Pas besoin de hedge si profit
        
        return {
            "total_spot_pnl": total_spot_pnl,
            "total_hedge_pnl": total_hedge_pnl,
            "net_pnl": net_pnl,
            "hedge_efficiency": hedge_efficiency,
            "total_exposure": self.total_exposure,
            "hedged_percentage": (self.hedged_exposure / self.total_exposure * 100) if self.total_exposure > 0 else 0
        }
    
    def rebalance_hedges(self, current_prices: Dict[str, float]):
        """Rééquilibre les hedges selon conditions actuelles"""
        stats = self.update_positions(current_prices)
        
        # Si hedge inefficace, ajuster
        if stats["hedge_efficiency"] < 70 and self.mode == HedgingMode.DYNAMIC:
            print("🔄 Rebalancing hedges...")
            # Fermer hedges actuels et créer nouveaux
            for hedge in self.hedge_positions:
                hedge.active = False
            
            # Recréer hedges
            for spot_pos in self.spot_positions:
                if spot_pos.active:
                    self._create_hedge(spot_pos)
    
    def get_statistics(self) -> Dict:
        """Stats du hedging"""
        active_spots = sum(1 for p in self.spot_positions if p.active)
        active_hedges = sum(1 for p in self.hedge_positions if p.active)
        
        return {
            "mode": self.mode.value,
            "active_spot_positions": active_spots,
            "active_hedge_positions": active_hedges,
            "total_exposure": self.total_exposure,
            "hedged_exposure": self.hedged_exposure,
            "hedge_ratio": self.hedged_exposure / self.total_exposure if self.total_exposure > 0 else 0,
            "hedge_strategies": {
                "futures": sum(1 for h in self.hedge_positions if h.strategy == "futures"),
                "grid": sum(1 for h in self.hedge_positions if h.strategy == "grid"),
                "dca": sum(1 for h in self.hedge_positions if h.strategy == "dca")
            }
        }


# Exemple d'utilisation
if __name__ == "__main__":
    hedger = CrossStrategyHedger(mode=HedgingMode.MODERATE)
    
    # Ajouter position spot
    print("=== Adding Spot Position ===")
    result = hedger.add_spot_position(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.5,
        entry_price=50000
    )
    print(f"✅ {result}")
    
    # Stats
    print("\n📊 Stats:", hedger.get_statistics())
    
    # Update avec nouveaux prix
    print("\n=== Price Update ===")
    current_prices = {"BTCUSDT": 48000}  # Prix baisse
    update = hedger.update_positions(current_prices)
    print(f"Spot PnL: ${update['total_spot_pnl']:.2f}")
    print(f"Hedge PnL: ${update['total_hedge_pnl']:.2f}")
    print(f"Net PnL: ${update['net_pnl']:.2f}")
    print(f"Hedge Efficiency: {update['hedge_efficiency']:.1f}%")
