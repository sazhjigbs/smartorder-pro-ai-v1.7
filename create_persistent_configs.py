#!/usr/bin/env python3
"""
Création des fichiers de configuration persistants pour le Dashboard
"""
import json
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path("/opt/smartorder-pro/config")
CONFIG_DIR.mkdir(exist_ok=True)

# Liste des 14 stratégies AI
STRATEGIES = [
    # SPOT Strategies
    {"id": "rsi_oversold", "name": "RSI Oversold Hunter", "type": "SPOT", "enabled": False, "score": 0},
    {"id": "macd_crossover", "name": "MACD Crossover", "type": "SPOT", "enabled": False, "score": 0},
    {"id": "bollinger_bounce", "name": "Bollinger Bounce", "type": "SPOT", "enabled": False, "score": 0},
    {"id": "support_resistance", "name": "Support/Resistance", "type": "SPOT", "enabled": False, "score": 0},
    {"id": "volume_breakout", "name": "Volume Breakout", "type": "SPOT", "enabled": False, "score": 0},
    
    # FUTURES Strategies
    {"id": "trend_following", "name": "Trend Following", "type": "FUTURES", "enabled": False, "score": 0},
    {"id": "mean_reversion", "name": "Mean Reversion", "type": "FUTURES", "enabled": False, "score": 0},
    {"id": "scalping_ai", "name": "AI Scalping", "type": "FUTURES", "enabled": False, "score": 0},
    {"id": "momentum_surge", "name": "Momentum Surge", "type": "FUTURES", "enabled": False, "score": 0},
    
    # HYBRID Strategies
    {"id": "arbitrage_detector", "name": "Arbitrage Detector", "type": "HYBRID", "enabled": False, "score": 0},
    {"id": "hedging_ai", "name": "AI Hedging", "type": "HYBRID", "enabled": False, "score": 0},
    {"id": "correlation_trader", "name": "Correlation Trader", "type": "HYBRID", "enabled": False, "score": 0},
    {"id": "liquidity_hunter", "name": "Liquidity Hunter", "type": "HYBRID", "enabled": False, "score": 0},
    {"id": "adaptive_composite", "name": "Adaptive Composite", "type": "HYBRID", "enabled": False, "score": 0},
]

# Configuration des exchanges
EXCHANGES = [
    {"id": "bybit_spot", "name": "Bybit Spot", "enabled": True},
    {"id": "bybit_futures", "name": "Bybit Futures", "enabled": True},
]

# strategies_state.json
strategies_state = {
    "strategies": STRATEGIES,
    "last_update": datetime.now().isoformat(),
    "auto_mode": {
        "spot": False,
        "futures": False
    }
}

with open(CONFIG_DIR / "strategies_state.json", 'w') as f:
    json.dump(strategies_state, f, indent=2)
print("✅ strategies_state.json créé")

# exchanges_state.json
exchanges_state = {
    "exchanges": EXCHANGES,
    "last_update": datetime.now().isoformat()
}

with open(CONFIG_DIR / "exchanges_state.json", 'w') as f:
    json.dump(exchanges_state, f, indent=2)
print("✅ exchanges_state.json créé")

# dashboard_settings.json
dashboard_settings = {
    "theme": "dark",
    "refresh_interval": 5000,
    "show_indicators": True,
    "show_signals": True,
    "last_update": datetime.now().isoformat()
}

with open(CONFIG_DIR / "dashboard_settings.json", 'w') as f:
    json.dump(dashboard_settings, f, indent=2)
print("✅ dashboard_settings.json créé")

print("\n📊 Fichiers de configuration créés avec succès:")
print(f"  - {CONFIG_DIR / 'strategies_state.json'}")
print(f"  - {CONFIG_DIR / 'exchanges_state.json'}")
print(f"  - {CONFIG_DIR / 'dashboard_settings.json'}")
