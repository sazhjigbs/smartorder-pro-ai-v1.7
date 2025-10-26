"""
SmartOrder PRO - Portfolio Rebalancer
Rééquilibre automatiquement le portfolio selon allocation cible
"""

import logging
from typing import Dict, List
from datetime import datetime

LOG = logging.getLogger("portfolio_rebalancer")
LOG.setLevel(logging.INFO)

class PortfolioRebalancer:
    """
    Maintient une allocation cible du portfolio
    
    Example:
    - Target: 50% BTC, 30% ETH, 20% USDT
    - Current: 60% BTC, 25% ETH, 15% USDT
    - Action: Vendre 10% BTC, Acheter 5% ETH, 5% USDT
    
    Bénéfice: "Sell high, buy low" automatique
    Frequency: Hebdomadaire ou mensuelle
    """
    
    def __init__(self, target_allocation: Dict[str, float]):
        """
        Args:
            target_allocation: {'BTC': 50.0, 'ETH': 30.0, 'USDT': 20.0}
        """
        self.target_allocation = target_allocation
        self.rebalance_threshold = 5.0  # Rebalance si deviation > 5%
        
        self.stats = {
            'total_rebalances': 0,
            'last_rebalance': None
        }
        
        LOG.info(f"PortfolioRebalancer initialized: {target_allocation}")
    
    def calculate_deviation(self, current_allocation: Dict[str, float]) -> Dict[str, float]:
        """Calcule la déviation entre allocation actuelle et cible"""
        deviations = {}
        for asset, target_pct in self.target_allocation.items():
            current_pct = current_allocation.get(asset, 0.0)
            deviations[asset] = current_pct - target_pct
        return deviations
    
    def should_rebalance(self, current_allocation: Dict[str, float]) -> bool:
        """Détermine si rebalancing nécessaire"""
        deviations = self.calculate_deviation(current_allocation)
        max_deviation = max(abs(d) for d in deviations.values())
        return max_deviation > self.rebalance_threshold
    
    def generate_rebalance_trades(self, current_allocation: Dict[str, float], 
                                 total_value: float) -> List[Dict]:
        """Génère les trades nécessaires pour rebalancer"""
        trades = []
        deviations = self.calculate_deviation(current_allocation)
        
        for asset, deviation in deviations.items():
            if abs(deviation) > 0.5:  # Ignorer petites deviations
                trade_value = total_value * (deviation / 100)
                
                if deviation > 0:
                    # Surpondéré, vendre
                    trades.append({
                        'asset': asset,
                        'action': 'SELL',
                        'amount_usdt': abs(trade_value),
                        'deviation': deviation
                    })
                else:
                    # Sous-pondéré, acheter
                    trades.append({
                        'asset': asset,
                        'action': 'BUY',
                        'amount_usdt': abs(trade_value),
                        'deviation': deviation
                    })
        
        self.stats['total_rebalances'] += 1
        self.stats['last_rebalance'] = datetime.now().isoformat()
        
        LOG.info(f"Generated {len(trades)} rebalance trades")
        return trades
    
    def get_stats(self) -> Dict:
        return {**self.stats}


_portfolio_rebalancers = {}

def get_portfolio_rebalancer(allocation: Dict[str, float]) -> PortfolioRebalancer:
    key = str(sorted(allocation.items()))
    if key not in _portfolio_rebalancers:
        _portfolio_rebalancers[key] = PortfolioRebalancer(allocation)
    return _portfolio_rebalancers[key]
