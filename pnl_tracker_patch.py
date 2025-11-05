import json
import os

def save_pnl_update(symbol, pnl):
    """Mise à jour pnl_tracker.json"""
    path = "/opt/smartorder-pro/config/pnl_tracker.json"
    try:
        pnl_data = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                pnl_data = json.load(f)
        pnl_data[symbol] = float(pnl)
        with open(path, "w") as f:
            json.dump(pnl_data, f, indent=4)
        print(f"[pnl_tracker] Updated {symbol}: {pnl}")
    except Exception as e:
        print(f"[pnl_tracker ERROR] {e}")
