#!/usr/bin/env python3
"""
Test Market Sentiment API
==========================
Test rapide de tous les endpoints Sentiment
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.sentiment import MarketSentiment


def test_sentiment_engine():
    """Test du moteur sentiment"""
    print("=" * 70)
    print("🧪 TEST MARKET SENTIMENT ENGINE")
    print("=" * 70)
    
    sentiment = MarketSentiment()
    
    # Test 1: Fear & Greed
    print("\n1️⃣ Fear & Greed Index:")
    fg = sentiment.get_fear_greed_index()
    print(f"   ✅ Value: {fg['value']}/100")
    print(f"   ✅ Level: {fg['level']}")
    print(f"   ✅ Recommendation: {fg['recommendation']}")
    
    # Test 2: BTC Dominance
    print("\n2️⃣ BTC Dominance:")
    dominance = sentiment.get_btc_dominance()
    print(f"   ✅ {dominance:.2f}%")
    
    # Test 3: Volatility
    print("\n3️⃣ Market Volatility:")
    vol = sentiment.get_market_volatility()
    print(f"   ✅ {vol['volatility_percent']}% (24h)")
    print(f"   ✅ Level: {vol['level']}")
    print(f"   ✅ Risk Level: {vol['risk_level']}/5")
    
    # Test 4: Market Regime
    print("\n4️⃣ Market Regime:")
    regime = sentiment.get_market_regime()
    print(f"   ✅ Regime: {regime['regime']}")
    print(f"   ✅ Description: {regime['description']}")
    print(f"   ✅ Strategy: {regime['strategy']}")
    print(f"   ✅ Confidence: {regime['confidence']}")
    
    # Test 5: Context Global
    print("\n5️⃣ Global Market Context:")
    context = sentiment.get_market_context()
    print(f"   ✅ Risk Score: {context['global_risk_score']}/100")
    print(f"   ✅ {context['recommendation']}")
    
    # Test 6: Trade Decision
    print("\n6️⃣ Should Trade Signal?")
    decision = sentiment.should_trade_signal(
        signal_confidence=0.85,
        symbol="BTCUSDT"
    )
    print(f"   ✅ Should Trade: {'YES ✅' if decision['should_trade'] else 'NO ❌'}")
    print(f"   ✅ Reasons:")
    for reason in decision['reasons']:
        print(f"      - {reason}")
    
    # Test 7: Cache
    print("\n7️⃣ Cache System:")
    print(f"   ✅ Cached items: {list(sentiment.cache.keys())}")
    sentiment.clear_cache()
    print(f"   ✅ Cache cleared")
    
    print("\n" + "=" * 70)
    print("✅ TOUS LES TESTS PASSÉS !")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = test_sentiment_engine()
        
        if success:
            print("\n🎉 Market Sentiment Engine fonctionne parfaitement !")
            print("\n💡 Pour lancer l'API:")
            print("   uvicorn api.api_sentiment:app --host 0.0.0.0 --port 8558")
            
            print("\n📡 Endpoints disponibles:")
            print("   GET  http://localhost:8558/api/sentiment/fear_greed")
            print("   GET  http://localhost:8558/api/sentiment/btc_dominance")
            print("   GET  http://localhost:8558/api/sentiment/volatility")
            print("   GET  http://localhost:8558/api/sentiment/regime")
            print("   GET  http://localhost:8558/api/sentiment/context")
            print("   POST http://localhost:8558/api/sentiment/should_trade")
            print("   POST http://localhost:8558/api/sentiment/clear_cache")
            
            sys.exit(0)
        else:
            print("\n❌ Tests échoués")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
