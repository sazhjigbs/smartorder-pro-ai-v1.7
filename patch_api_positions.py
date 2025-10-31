#!/usr/bin/env python3
"""Patch l'API pour lire les positions du Strategy Executor v2"""

import re

api_file = '/opt/smartorder-pro/api/main.py'

with open(api_file, 'r') as f:
    content = f.read()

# Patch 1: Changer chemin positions
content = re.sub(
    r'def get_positions\(\):.*?(?=\n@app\.get|$)',
    '''def get_positions():
    """Positions depuis Strategy Executor v2"""
    positions_file = "/opt/smartorder-pro/config/positions.json"
    if os.path.exists(positions_file):
        try:
            with open(positions_file, 'r') as f:
                all_positions = json.load(f)
            # Retourner uniquement positions ouvertes
            return [p for p in all_positions if p.get('status') == 'open']
        except:
            return []
    return []

''',
    content,
    flags=re.DOTALL
)

# Patch 2: Changer PnL pour lire depuis pnl_tracker.json
content = re.sub(
    r'def get_pnl\(\):.*?(?=\n@app\.get|$)',
    '''def get_pnl():
    """PnL depuis Strategy Executor v2"""
    pnl_file = "/opt/smartorder-pro/config/pnl_tracker.json"
    if os.path.exists(pnl_file):
        try:
            with open(pnl_file, 'r') as f:
                tracker = json.load(f)
            return {
                "total": tracker.get("total_pnl", 0.0),
                "today": tracker.get("total_pnl", 0.0),
                "by_strategy": tracker.get("by_strategy", {})
            }
        except:
            return {"total": 0.0, "today": 0.0}
    return {"total": 0.0, "today": 0.0}

''',
    content,
    flags=re.DOTALL
)

with open(api_file, 'w') as f:
    f.write(content)

print("✅ API patched successfully")
print("   - /api/positions → /opt/smartorder-pro/config/positions.json")
print("   - /api/pnl → /opt/smartorder-pro/config/pnl_tracker.json")
