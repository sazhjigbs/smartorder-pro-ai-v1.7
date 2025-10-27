"""
Test Script - Multi-Exchange Integration
Test tous les connecteurs et le router intelligent

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unified_trading_manager import UnifiedTradingManager
from core.exchange_router import ExchangeRouter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

LOG = logging.getLogger(__name__)


def test_connections():
    """Test connection to all configured exchanges"""
    LOG.info("=" * 60)
    LOG.info("TEST 1: Connection Test")
    LOG.info("=" * 60)
    
    manager = UnifiedTradingManager()
    
    results = {}
    
    for exchange_name, connector in manager.connectors.items():
        LOG.info(f"\nTesting {exchange_name.upper()}...")
        
        try:
            result = connector.test_connection()
            results[exchange_name] = result
            
            if result.get('success'):
                LOG.info(f"✅ {exchange_name} connection OK")
            else:
                LOG.error(f"❌ {exchange_name} connection FAILED: {result.get('error')}")
        
        except Exception as e:
            LOG.error(f"❌ {exchange_name} exception: {e}")
            results[exchange_name] = {'success': False, 'error': str(e)}
    
    # Summary
    LOG.info("\n" + "=" * 60)
    LOG.info("CONNECTION TEST SUMMARY")
    LOG.info("=" * 60)
    
    for exchange, result in results.items():
        status = "✅ OK" if result.get('success') else "❌ FAILED"
        LOG.info(f"{exchange.upper()}: {status}")
    
    return results


def test_tickers():
    """Test ticker data from all exchanges"""
    LOG.info("\n" + "=" * 60)
    LOG.info("TEST 2: Ticker Data")
    LOG.info("=" * 60)
    
    manager = UnifiedTradingManager()
    
    test_symbols = {
        'bybit': 'BTCUSDT',
        'binance': 'BTCUSDT',
        'okx': 'BTC-USDT',
        'kucoin': 'BTC-USDT'
    }
    
    results = {}
    
    for exchange_name, connector in manager.connectors.items():
        symbol = test_symbols.get(exchange_name)
        
        if not symbol:
            continue
        
        LOG.info(f"\nGetting {symbol} ticker from {exchange_name}...")
        
        try:
            ticker = connector.get_ticker(symbol)
            results[exchange_name] = ticker
            
            if ticker.get('success'):
                price = ticker.get('last_price', 0)
                LOG.info(f"✅ {exchange_name}: ${price:,.2f}")
            else:
                LOG.error(f"❌ {exchange_name}: {ticker.get('error')}")
        
        except Exception as e:
            LOG.error(f"❌ {exchange_name} exception: {e}")
            results[exchange_name] = {'success': False, 'error': str(e)}
    
    # Summary
    LOG.info("\n" + "=" * 60)
    LOG.info("TICKER TEST SUMMARY")
    LOG.info("=" * 60)
    
    for exchange, result in results.items():
        if result.get('success'):
            price = result.get('last_price', 0)
            LOG.info(f"{exchange.upper()}: ${price:,.2f}")
        else:
            LOG.info(f"{exchange.upper()}: FAILED")
    
    return results


def test_balances():
    """Test balance retrieval from all exchanges"""
    LOG.info("\n" + "=" * 60)
    LOG.info("TEST 3: Balance Retrieval")
    LOG.info("=" * 60)
    
    manager = UnifiedTradingManager()
    
    results = {}
    
    for exchange_name in manager.connectors.keys():
        LOG.info(f"\nGetting balance from {exchange_name}...")
        
        try:
            balance = manager.get_balance(exchange=exchange_name)
            results[exchange_name] = balance
            
            if balance:
                equity = balance.get('total_equity', 0)
                LOG.info(f"✅ {exchange_name}: ${equity:,.2f}")
            else:
                LOG.warning(f"⚠️ {exchange_name}: No balance data")
        
        except Exception as e:
            LOG.error(f"❌ {exchange_name} exception: {e}")
            results[exchange_name] = {'error': str(e)}
    
    # Summary
    LOG.info("\n" + "=" * 60)
    LOG.info("BALANCE TEST SUMMARY")
    LOG.info("=" * 60)
    
    total_equity = 0.0
    
    for exchange, balance in results.items():
        if balance and 'total_equity' in balance:
            equity = balance['total_equity']
            total_equity += equity
            LOG.info(f"{exchange.upper()}: ${equity:,.2f}")
        else:
            LOG.info(f"{exchange.upper()}: N/A")
    
    LOG.info(f"\nTOTAL EQUITY (ALL EXCHANGES): ${total_equity:,.2f}")
    
    return results


def test_router():
    """Test exchange router"""
    LOG.info("\n" + "=" * 60)
    LOG.info("TEST 4: Exchange Router")
    LOG.info("=" * 60)
    
    manager = UnifiedTradingManager()
    router = ExchangeRouter(manager)
    
    test_symbol = 'BTCUSDT'
    
    # Test different selection criteria
    criteria_list = ['fees', 'liquidity', 'auto']
    
    results = {}
    
    for criteria in criteria_list:
        LOG.info(f"\nSelecting best exchange for {test_symbol} (criteria: {criteria})...")
        
        try:
            best = router.get_best_exchange(test_symbol, criteria=criteria)
            results[criteria] = best
            LOG.info(f"✅ Best exchange ({criteria}): {best}")
        
        except Exception as e:
            LOG.error(f"❌ Router failed ({criteria}): {e}")
            results[criteria] = None
    
    # Test best price across exchanges
    LOG.info(f"\nGetting best price for {test_symbol} across all exchanges...")
    
    try:
        best_prices = router.get_best_price(test_symbol)
        
        if best_prices['best_bid']['exchange']:
            LOG.info(f"✅ Best BID: ${best_prices['best_bid']['price']:,.2f} on {best_prices['best_bid']['exchange']}")
        
        if best_prices['best_ask']['exchange']:
            LOG.info(f"✅ Best ASK: ${best_prices['best_ask']['price']:,.2f} on {best_prices['best_ask']['exchange']}")
        
        LOG.info(f"✅ SPREAD: ${best_prices['spread']:,.2f}")
    
    except Exception as e:
        LOG.error(f"❌ Best price failed: {e}")
    
    return results


def run_all_tests():
    """Run all tests"""
    LOG.info("🚀 STARTING MULTI-EXCHANGE TESTS")
    LOG.info("=" * 60)
    
    # Test 1: Connections
    try:
        connection_results = test_connections()
    except Exception as e:
        LOG.error(f"❌ Connection test failed: {e}")
    
    # Test 2: Tickers
    try:
        ticker_results = test_tickers()
    except Exception as e:
        LOG.error(f"❌ Ticker test failed: {e}")
    
    # Test 3: Balances
    try:
        balance_results = test_balances()
    except Exception as e:
        LOG.error(f"❌ Balance test failed: {e}")
    
    # Test 4: Router
    try:
        router_results = test_router()
    except Exception as e:
        LOG.error(f"❌ Router test failed: {e}")
    
    # Final summary
    LOG.info("\n" + "=" * 60)
    LOG.info("🎉 ALL TESTS COMPLETED")
    LOG.info("=" * 60)
    LOG.info("\n⚠️ NOTE: If any test failed, check your .env configuration")
    LOG.info("Make sure API keys are set for the exchanges you want to test")


if __name__ == "__main__":
    run_all_tests()
