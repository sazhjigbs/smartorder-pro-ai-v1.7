#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

config_dir = Path('/opt/smartorder-pro/config')
config_dir.mkdir(exist_ok=True)

# paper_wallet.json
with open(config_dir / 'paper_wallet.json', 'w') as f:
    json.dump({
        'balance_usdt': 10000.0,
        'total_pnl': 0.0,
        'open_positions': 0,
        'last_update': datetime.now().isoformat()
    }, f, indent=2)

# pnl_tracker.json
with open(config_dir / 'pnl_tracker.json', 'w') as f:
    json.dump({
        'total_pnl': 0.0,
        'daily_pnl': 0.0,
        'weekly_pnl': 0.0,
        'trades_count': 0,
        'win_rate': 0.0,
        'last_update': datetime.now().isoformat()
    }, f, indent=2)

# positions.json
with open(config_dir / 'positions.json', 'w') as f:
    json.dump({
        'positions': [],
        'total_value': 0.0,
        'last_update': datetime.now().isoformat()
    }, f, indent=2)

print('✅ JSON files created successfully')
print('Content of pnl_tracker.json:')
with open(config_dir / 'pnl_tracker.json', 'r') as f:
    print(f.read())
