"""
Exchange Router - Smart Exchange Selection
Sélectionne automatiquement le meilleur exchange selon plusieurs critères

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

LOG = logging.getLogger(__name__)


class ExchangeRouter:
    """
    Router intelligent pour sélectionner le meilleur exchange
    
    Critères de sélection:
    - Fees (maker/taker)
    - Liquidité (volume 24h)
    - Latency (ping)
    - Health status
    - Disponibilité du trading pair
    """
    
    def __init__(self, unified_manager):
        """
        Initialize Exchange Router
        
        Args:
            unified_manager: UnifiedTradingManager instance
        """
        self.manager = unified_manager
        self.config = self._load_exchange_config()
        
        LOG.info("✅ Exchange Router initialized")
    
    def _load_exchange_config(self) -> Dict:
        """Load exchange configuration from JSON"""
        config_path = Path(__file__).parent.parent / 'config' / 'exchanges.json'
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            LOG.error(f"❌ Failed to load exchange config: {e}")
            return {}
    
    def get_best_exchange(self, 
                          symbol: str,
                          criteria: str = 'fees') -> str:
        """
        Sélectionne le meilleur exchange pour un symbole donné
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            criteria: 'fees' | 'liquidity' | 'latency' | 'auto'
        
        Returns:
            Exchange name (e.g., 'binance')
        """
        available_exchanges = []
        
        # Check which exchanges are available and support the symbol
        for exchange_name, connector in self.manager.connectors.items():
            exchange_config = self.config.get(exchange_name, {})
            
            # Check if symbol is supported
            if self._is_symbol_supported(exchange_name, symbol):
                # Check health
                if self.manager.health_monitor.is_healthy(exchange_name):
                    available_exchanges.append({
                        'name': exchange_name,
                        'fees': exchange_config.get('fees', {}),
                        'config': exchange_config
                    })
        
        if not available_exchanges:
            LOG.warning(f"⚠️ No exchange available for {symbol}")
            return None
        
        # Select based on criteria
        if criteria == 'fees':
            return self._select_by_fees(available_exchanges)
        elif criteria == 'liquidity':
            return self._select_by_liquidity(available_exchanges)
        elif criteria == 'latency':
            return self._select_by_latency(available_exchanges)
        else:  # auto
            return self._select_auto(available_exchanges)
    
    def _is_symbol_supported(self, exchange: str, symbol: str) -> bool:
        """Check if symbol is supported by exchange"""
        exchange_config = self.config.get(exchange, {})
        symbols = exchange_config.get('symbols', [])
        
        # Normalize symbol format
        normalized_symbol = self._normalize_symbol(symbol, exchange)
        
        return normalized_symbol in symbols
    
    def _normalize_symbol(self, symbol: str, exchange: str) -> str:
        """
        Normalize symbol format for exchange
        
        Examples:
        - Bybit/Binance: BTCUSDT
        - OKX/KuCoin: BTC-USDT
        """
        if exchange in ['okx', 'kucoin']:
            # Convert BTCUSDT -> BTC-USDT
            if '-' not in symbol:
                # Assuming USDT pair
                base = symbol.replace('USDT', '')
                return f"{base}-USDT"
        else:
            # Convert BTC-USDT -> BTCUSDT
            return symbol.replace('-', '')
        
        return symbol
    
    def _select_by_fees(self, exchanges: List[Dict]) -> str:
        """Select exchange with lowest fees"""
        best = min(exchanges, key=lambda x: x['fees'].get('taker', 1.0))
        LOG.info(f"✅ Selected {best['name']} (lowest fees: {best['fees'].get('taker')*100:.2f}%)")
        return best['name']
    
    def _select_by_liquidity(self, exchanges: List[Dict]) -> str:
        """Select exchange with highest liquidity (simplified)"""
        # For now, Binance typically has highest liquidity
        for ex in exchanges:
            if ex['name'] == 'binance':
                LOG.info(f"✅ Selected binance (highest liquidity)")
                return 'binance'
        
        # Fallback to first available
        LOG.info(f"✅ Selected {exchanges[0]['name']} (fallback)")
        return exchanges[0]['name']
    
    def _select_by_latency(self, exchanges: List[Dict]) -> str:
        """Select exchange with lowest latency"""
        # TODO: Implement actual latency testing
        # For now, return first available
        LOG.info(f"✅ Selected {exchanges[0]['name']} (latency test not implemented)")
        return exchanges[0]['name']
    
    def _select_auto(self, exchanges: List[Dict]) -> str:
        """
        Auto selection using weighted score
        
        Weight:
        - Fees: 50%
        - Liquidity: 30%
        - Latency: 20%
        """
        scores = {}
        
        for ex in exchanges:
            # Fees score (lower is better)
            fees = ex['fees'].get('taker', 0.001)
            fees_score = (0.001 - fees) * 1000  # Normalize
            
            # Liquidity score (simple heuristic)
            liquidity_score = 100 if ex['name'] == 'binance' else 80
            
            # Latency score (placeholder)
            latency_score = 50
            
            # Weighted total
            total_score = (fees_score * 0.5) + (liquidity_score * 0.3) + (latency_score * 0.2)
            
            scores[ex['name']] = total_score
        
        # Get best
        best = max(scores, key=scores.get)
        LOG.info(f"✅ Auto-selected {best} (score: {scores[best]:.2f})")
        
        return best
    
    def route_order(self,
                    symbol: str,
                    side: str,
                    order_type: str,
                    quantity: float,
                    price: float = None,
                    preferred_exchange: str = None) -> Dict:
        """
        Route order to best exchange
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: Order quantity
            price: Limit price (optional)
            preferred_exchange: Preferred exchange (optional)
        
        Returns:
            Order result with exchange info
        """
        # Use preferred exchange if specified
        if preferred_exchange and preferred_exchange in self.manager.connectors:
            exchange = preferred_exchange
        else:
            # Auto-select best exchange
            exchange = self.get_best_exchange(symbol, criteria='auto')
        
        if not exchange:
            return {
                'success': False,
                'error': 'No exchange available'
            }
        
        # Normalize symbol for exchange
        normalized_symbol = self._normalize_symbol(symbol, exchange)
        
        LOG.info(f"🔄 Routing order to {exchange}: {side} {quantity} {normalized_symbol}")
        
        # Place order via unified manager
        result = self.manager.place_order(
            exchange=exchange,
            symbol=normalized_symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        # Add exchange info to result
        result['exchange'] = exchange
        result['original_symbol'] = symbol
        
        return result
    
    def get_best_price(self, symbol: str) -> Dict:
        """
        Get best price across all exchanges
        
        Args:
            symbol: Trading pair
        
        Returns:
            {
                'best_bid': {'exchange': 'binance', 'price': 50000},
                'best_ask': {'exchange': 'bybit', 'price': 50010}
            }
        """
        best_bid = {'exchange': None, 'price': 0}
        best_ask = {'exchange': None, 'price': float('inf')}
        
        for exchange_name, connector in self.manager.connectors.items():
            if not self.manager.health_monitor.is_healthy(exchange_name):
                continue
            
            # Get ticker
            normalized_symbol = self._normalize_symbol(symbol, exchange_name)
            ticker = self.manager.get_ticker(exchange=exchange_name, symbol=normalized_symbol)
            
            if ticker.get('success'):
                bid = ticker.get('bid_price', 0)
                ask = ticker.get('ask_price', float('inf'))
                
                # Update best bid (highest)
                if bid > best_bid['price']:
                    best_bid = {'exchange': exchange_name, 'price': bid}
                
                # Update best ask (lowest)
                if ask < best_ask['price']:
                    best_ask = {'exchange': exchange_name, 'price': ask}
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': best_ask['price'] - best_bid['price']
        }


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from core.unified_trading_manager import UnifiedTradingManager
    
    manager = UnifiedTradingManager()
    router = ExchangeRouter(manager)
    
    # Test routing
    best = router.get_best_exchange('BTCUSDT', criteria='fees')
    print(f"Best exchange for BTCUSDT: {best}")
    
    # Test best price
    prices = router.get_best_price('BTCUSDT')
    print(f"Best prices: {prices}")
