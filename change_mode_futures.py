#!/usr/bin/env python3
import json

# Charger config
with open('/opt/smartorder-pro/config/trading_modes.json', 'r') as f:
    config = json.load(f)

# Changer mode
old_mode = config['current_mode']
config['current_mode'] = 'futures'

# Sauvegarder
with open('/opt/smartorder-pro/config/trading_modes.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"Mode changé: {old_mode} → futures")
