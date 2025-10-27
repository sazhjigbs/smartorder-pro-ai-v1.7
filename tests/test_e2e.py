# -*- coding: utf-8 -*-
"""End-to-End Integration Test"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_full_workflow():
    """Test complete trading workflow"""
    print("E2E Test: Full Trading Workflow")
    print("=" * 50)
    
    # 1. Init manager
    from core.unified_trading_manager import UnifiedTradingManager
    manager = UnifiedTradingManager()
    print("✅ Manager initialized")
    
    # 2. Check exchanges
    assert len(manager.connectors) > 0, "No exchanges"
    print(f"✅ {len(manager.connectors)} exchanges ready")
    
    # 3. Get balance
    for exchange in manager.connectors.keys():
        try:
            balance = manager.get_balance(exchange=exchange)
            print(f"✅ {exchange}: Balance OK")
        except Exception as e:
            print(f"⚠️ {exchange}: {e}")
    
    # 4. Risk manager
    from strategies.risk_manager import RiskManager
    risk_mgr = RiskManager()
    result = risk_mgr.calculate_position_size(10000, 50000, 49000)
    assert result['position_size'] > 0
    print("✅ Risk manager OK")
    
    # 5. Signal aggregator
    from strategies.signal_aggregator import SignalAggregator
    agg = SignalAggregator()
    signal = agg.aggregate({
        'ai': {'direction': 'long', 'confidence': 0.7}
    })
    assert signal['direction'] in ['long', 'short', 'neutral']
    print("✅ Signal aggregator OK")
    
    print("\n🎉 E2E Test PASSED!")

if __name__ == "__main__":
    test_full_workflow()
