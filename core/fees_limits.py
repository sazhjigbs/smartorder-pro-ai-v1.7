#!/usr/bin/env python3
"""
💰 SAFELOGIC SmartOrder PRO — Fees & Limits Module
Gestion ccxt + cache des contraintes par exchange
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class ExchangeFeesLimits:
    def __init__(self):
        self.cache_file = "data/exchange_constraints.json"
        self.cache_duration = 3600  # 1 hour cache
        self.data = {}
        
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        # Load cached data
        self.load_cache()
        
    def load_cache(self):
        """Load cached exchange data"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    cached = json.load(f)
                
                # Check if cache is still valid
                cache_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
                    self.data = cached.get('data', {})
                    return
        except Exception as e:
            print(f"⚠️ Error loading cache: {str(e)}")
    
    def save_cache(self):
        """Save data to cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': self.data
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error saving cache: {str(e)}")
    
    def get_exchange_limits(self, exchange: str, symbol: str):
        """Get exchange limits for a symbol"""
        
        # Mock data for now (in production, would use ccxt)
        mock_limits = {
            "bybit": {
                "BTCUSDT": {
                    "minNotional": 10,
                    "minQty": 0.001,
                    "stepSize": 0.001,
                    "tickSize": 0.1,
                    "makerFee": 0.0001,
                    "takerFee": 0.0006
                },
                "ETHUSDT": {
                    "minNotional": 10,
                    "minQty": 0.01,
                    "stepSize": 0.01,
                    "tickSize": 0.01,
                    "makerFee": 0.0001,
                    "takerFee": 0.0006
                }
            },
            "binance": {
                "BTCUSDT": {
                    "minNotional": 10,
                    "minQty": 0.00001,
                    "stepSize": 0.00001,
                    "tickSize": 0.01,
                    "makerFee": 0.0001,
                    "takerFee": 0.0004
                },
                "ETHUSDT": {
                    "minNotional": 10,
                    "minQty": 0.0001,
                    "stepSize": 0.0001,
                    "tickSize": 0.01,
                    "makerFee": 0.0001,
                    "takerFee": 0.0004
                }
            },
            "kucoin": {
                "BTCUSDT": {
                    "minNotional": 1,
                    "minQty": 0.00001,
                    "stepSize": 0.00001,
                    "tickSize": 0.1,
                    "makerFee": 0.0001,
                    "takerFee": 0.0001
                },
                "ETHUSDT": {
                    "minNotional": 1,
                    "minQty": 0.0001,
                    "stepSize": 0.0001,
                    "tickSize": 0.01,
                    "makerFee": 0.0001,
                    "takerFee": 0.0001
                }
            }
        }
        
        return mock_limits.get(exchange, {}).get(symbol, {})
    
    def apply_min_notional(self, exchange: str, symbol: str, quantity: float, price: float):
        """Apply minimum notional constraints"""
        limits = self.get_exchange_limits(exchange, symbol)
        min_notional = limits.get('minNotional', 10)
        
        notional_value = quantity * price
        
        if notional_value < min_notional:
            # Increase quantity to meet minimum
            required_qty = min_notional / price
            return max(required_qty, quantity)
        
        return quantity
    
    def get_trading_fees(self, exchange: str, symbol: str, is_maker: bool = False):
        """Get trading fees for exchange/symbol"""
        limits = self.get_exchange_limits(exchange, symbol)
        
        if is_maker:
            return limits.get('makerFee', 0.0001)
        else:
            return limits.get('takerFee', 0.0006)

# Global instance
fees_limits = ExchangeFeesLimits()

def get_symbol_constraints(exchange: str, symbol: str):
    """Get symbol constraints for exchange"""
    return fees_limits.get_exchange_limits(exchange, symbol)

def apply_min_notional(exchange: str, symbol: str, quantity: float, price: float):
    """Apply minimum notional requirements"""
    return fees_limits.apply_min_notional(exchange, symbol, quantity, price)

def get_trading_fees(exchange: str, symbol: str, is_maker: bool = False):
    """Get trading fees"""
    return fees_limits.get_trading_fees(exchange, symbol, is_maker)

if __name__ == "__main__":
    # Test
    print("🧪 Testing Fees & Limits...")
    
    constraints = get_symbol_constraints("bybit", "BTCUSDT")
    print(f"BTCUSDT constraints: {constraints}")
    
    adj_qty = apply_min_notional("bybit", "BTCUSDT", 0.0001, 67000)
    print(f"Adjusted quantity: {adj_qty}")
    
    fees = get_trading_fees("bybit", "BTCUSDT")
    print(f"Trading fees: {fees}")