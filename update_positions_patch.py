import json
import os
from datetime import datetime

def update_positions(symbol, strategy, amount, entry, current, sl, tp, pnl):
    """Mise à jour du fichier positions.json"""
    path = "/opt/smartorder-pro/config/positions.json"
    data = {
        "symbol": symbol,
        "strategy": strategy,
        "amount": amount,
        "entry": entry,
        "current": current,
        "sl": sl,
        "tp": tp,
        "pnl": pnl,
        "timestamp": datetime.now().isoformat()
    }
    try:
        positions = []
        if os.path.exists(path):
            with open(path, "r") as f:
                positions = json.load(f)
        positions.append(data)
        positions = positions[-50:]
        with open(path, "w") as f:
            json.dump(positions, f, indent=4)
        print(f"[update_positions] OK {symbol}")
    except Exception as e:
        print(f"[update_positions ERROR] {e}")
