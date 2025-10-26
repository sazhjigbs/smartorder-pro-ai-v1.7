"""
SmartOrder PRO - Market Making Strategy
Fournit de la liquidité et capture le spread bid-ask
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

LOG = logging.getLogger("market_making")
LOG.setLevel(logging.INFO)

class MarketMakingStrategy:
    """
    Market Making: Place simultanément ordres buy et sell autour du prix mid
    
    Stratégie:
    - Mid Price: $67,000
    - Spread: 0.1% ($67)
    - Bid: $66,966.50 (-0.05%)
    - Ask: $67,033.50 (+0.05%)
    - Profit par cycle: $67 (0.1%)
    
    ROI: 20-50% APY si volatilité modérée
    Risque: Inventory risk (rester coincé avec position)
    """
    
    def __init__(self, symbol: str, spread_pct: float = 0.1, max_position_size: float = 10000):
        self.symbol = symbol
        self.spread_pct = spread_pct
        self.max_position_size = max_position_size
        
        self.active_bids = []
        self.active_asks = []
        self.inventory = 0.0
        self.realized_pnl = 0.0
        
        self.stats = {
            'total_fills': 0,
            'buy_fills': 0,
            'sell_fills': 0,
            'total_profit': 0.0,
            'avg_spread_captured': 0.0
        }
        
        LOG.info(f"MarketMakingStrategy initialized: {symbol} spread={spread_pct}%")
    
    def quote_market(self, mid_price: float, size: float) -> Dict:
        """Place des ordres bid et ask autour du mid price"""
        half_spread = mid_price * (self.spread_pct / 100) / 2
        
        bid_price = mid_price - half_spread
        ask_price = mid_price + half_spread
        
        bid_order = {
            'side': 'BUY',
            'price': round(bid_price, 2),
            'quantity': size / bid_price,
            'status': 'ACTIVE',
            'timestamp': datetime.now().isoformat()
        }
        
        ask_order = {
            'side': 'SELL',
            'price': round(ask_price, 2),
            'quantity': size / ask_price,
            'status': 'ACTIVE',
            'timestamp': datetime.now().isoformat()
        }
        
        self.active_bids.append(bid_order)
        self.active_asks.append(ask_order)
        
        LOG.info(f"Market quoted: Bid {bid_price:.2f} | Ask {ask_price:.2f} (spread: {self.spread_pct}%)")
        
        return {'bid': bid_order, 'ask': ask_order}
    
    def check_fills(self, current_price: float, trade_volume: float = 0):
        """Vérifie si des ordres sont remplis"""
        # Check bids
        for bid in self.active_bids:
            if bid['status'] == 'ACTIVE' and current_price <= bid['price']:
                bid['status'] = 'FILLED'
                self.inventory += bid['quantity']
                self.stats['buy_fills'] += 1
                self.stats['total_fills'] += 1
                LOG.info(f"Bid filled @ {bid['price']}")
        
        # Check asks
        for ask in self.active_asks:
            if ask['status'] == 'ACTIVE' and current_price >= ask['price']:
                ask['status'] = 'FILLED'
                self.inventory -= ask['quantity']
                
                # Calculer profit
                spread_captured = (ask['price'] - current_price) * ask['quantity']
                self.realized_pnl += spread_captured
                self.stats['sell_fills'] += 1
                self.stats['total_fills'] += 1
                self.stats['total_profit'] += spread_captured
                
                LOG.info(f"Ask filled @ {ask['price']} (+${spread_captured:.2f})")
        
        # Update avg spread
        if self.stats['total_fills'] > 0:
            self.stats['avg_spread_captured'] = self.stats['total_profit'] / self.stats['total_fills']
    
    def manage_inventory(self, current_price: float) -> Optional[Dict]:
        """Gère le risque d'inventaire"""
        inventory_value = abs(self.inventory) * current_price
        
        if inventory_value > self.max_position_size:
            # Inventory trop élevé, réduire
            action = 'REDUCE_LONG' if self.inventory > 0 else 'REDUCE_SHORT'
            return {
                'action': action,
                'quantity': abs(self.inventory) * 0.5,  # Réduire de 50%
                'reason': f'Inventory risk: ${inventory_value:.2f} > ${self.max_position_size:.2f}'
            }
        
        return None
    
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            'current_inventory': self.inventory,
            'realized_pnl': round(self.realized_pnl, 2),
            'fill_rate': round((self.stats['total_fills'] / max(len(self.active_bids) + len(self.active_asks), 1)) * 100, 1)
        }


_market_makers = {}

def get_market_maker(symbol: str, spread: float = 0.1) -> MarketMakingStrategy:
    key = f"{symbol}_{spread}"
    if key not in _market_makers:
        _market_makers[key] = MarketMakingStrategy(symbol, spread)
    return _market_makers[key]


if __name__ == "__main__":
    print("=" * 60)
    print("Market Making Strategy - Test")
    print("=" * 60)
    
    mm = MarketMakingStrategy("BTCUSDT", spread_pct=0.1)
    
    mid_price = 67000.0
    
    # Quote le marché
    print(f"\n📊 Quoting market @ ${mid_price:,.0f}...")
    orders = mm.quote_market(mid_price, size=1000.0)
    
    print(f"   Bid: ${orders['bid']['price']:,.2f}")
    print(f"   Ask: ${orders['ask']['price']:,.2f}")
    print(f"   Spread: ${orders['ask']['price'] - orders['bid']['price']:.2f}")
    
    # Simuler des fills
    print(f"\n⚡ Simulation de fills...")
    
    # Prix touche le bid
    mm.check_fills(66966.0)
    
    # Prix touche l'ask
    mm.check_fills(67034.0)
    
    # Stats
    stats = mm.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Total fills: {stats['total_fills']}")
    print(f"   Buy/Sell: {stats['buy_fills']}/{stats['sell_fills']}")
    print(f"   Realized PnL: ${stats['realized_pnl']:.2f}")
    print(f"   Current inventory: {stats['current_inventory']:.4f}")
    print(f"   Fill rate: {stats['fill_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
