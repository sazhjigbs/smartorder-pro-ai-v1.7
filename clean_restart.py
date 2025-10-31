#!/usr/bin/env python3
"""Clean restart - Reset et relance propre"""
import json
import os
from datetime import datetime

# Reset state
state = {
    "mode": "PAPER",
    "paused": False,
    "active_strategies": ["Grid Trading", "DCA Strategy", "Scalping"],
    "balance": 10000,
    "total_value": 10000,
    "pnl": {
        "total": 0,
        "daily": 0,
        "weekly": 0,
        "monthly": 0,
        "by_strategy": {
            "Grid Trading": 0,
            "DCA Strategy": 0,
            "Scalping": 0,
            "Trend Following": 0
        }
    },
    "positions": [],
    "trades_count": 0,
    "last_update": datetime.now().isoformat()
}

# Reset auto trading
auto_state = {
    "mode": "HYBRID",
    "spot": {
        "balance": 5000,
        "positions": {},
        "capital": 5000
    },
    "futures": {
        "balance": 5000,
        "positions": {},
        "capital": 5000
    },
    "timestamp": datetime.now().isoformat()
}

# Save
os.makedirs('/opt/smartorder-pro/data', exist_ok=True)

with open('/opt/smartorder-pro/data/state.json', 'w') as f:
    json.dump(state, f, indent=2)

with open('/opt/smartorder-pro/data/auto_trading_state.json', 'w') as f:
    json.dump(auto_state, f, indent=2)

print("✅ NETTOYAGE COMPLET")
print("=" * 60)
print(f"📊 État principal reset: ${state['balance']:,.0f}")
print(f"⚡ Stratégies actives: {', '.join(state['active_strategies'])}")
print(f"🔀 Mode AUTO HYBRID reset")
print(f"   - SPOT: ${auto_state['spot']['balance']:,.0f}")
print(f"   - FUTURES: ${auto_state['futures']['balance']:,.0f}")
print("=" * 60)
print("\n✅ Prêt à relancer!")
