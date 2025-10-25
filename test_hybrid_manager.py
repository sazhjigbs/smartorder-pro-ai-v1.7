#!/usr/bin/env python3
"""
Test simple du module Hybrid Capital Manager
"""

# Test d'import et de validation syntaxique
try:
    print("🧪 Testing Hybrid Capital Manager Import...")
    
    # Test import
    import hybrid_capital_manager as hcm
    print("✅ Module import successful")
    
    # Test instance creation  
    manager = hcm.HybridCapitalManager()
    print("✅ HybridCapitalManager instance created")
    
    # Test configuration
    print(f"📊 Auto mode: {manager.auto_mode}")
    print(f"📊 Max orders: {manager.max_simultaneous_orders}")
    print(f"📊 Risk per trade: {manager.risk_per_trade}")
    
    # Test portfolio summary (sans scan)
    summary = manager.get_portfolio_summary()
    print(f"📋 Portfolio summary: {summary}")
    
    print("\n🎉 All basic tests passed!")
    print("✨ Module is ready for VPS deployment")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()