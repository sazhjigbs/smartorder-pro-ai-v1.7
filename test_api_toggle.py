import json
from pathlib import Path

CONFIG_PATH = Path('/opt/smartorder-pro/config')

def read_json(filename, default=None):
    try:
        with open(CONFIG_PATH / filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f'Error reading {filename}: {e}')
        return default if default is not None else {}

# Simulate toggle_strategy function
strategy_id = 'grid_trading'
print(f'Testing toggle for: {strategy_id}')

data = read_json('trading_modes.json')
print(f'Data loaded: {type(data)}')
print(f'Data keys: {list(data.keys())[:5]}')

if not data or not isinstance(data, dict):
    print('ERROR: Invalid config format')
    exit(1)

updated = False
new_state = None

print('\nIterating through modes...')
for mode in ['spot', 'futures', 'hybrid']:
    mode_strategies = data.get('strategies', {}).get(mode, [])
    print(f'  Mode {mode}: type={type(mode_strategies)}, is_list={isinstance(mode_strategies, list)}')
    
    if not isinstance(mode_strategies, list):
        print(f'    Skipping {mode} (not a list)')
        continue
    
    print(f'    Iterating {len(mode_strategies)} strategies in {mode}...')
    for idx, strat in enumerate(mode_strategies):
        print(f'      [{idx}] type={type(strat)}', end='')
        if isinstance(strat, dict):
            sid = strat.get('id')
            slabel = strat.get('label')
            print(f' id={sid}, label={slabel}', end='')
            if sid == strategy_id or slabel == strategy_id:
                print(f' ← MATCH!')
                current_enabled = strat.get('enabled', False)
                strat['enabled'] = not current_enabled
                new_state = strat['enabled']
                updated = True
                print(f'      Toggled from {current_enabled} to {new_state}')
                break
            else:
                print()
        else:
            print(f' ERROR: not a dict!')
            print(f'      Content: {strat}')
            exit(1)
    
    if updated:
        print(f'  Breaking after finding match in {mode}')
        break

if updated:
    print(f'\n✅ SUCCESS: {strategy_id} toggled to {new_state}')
else:
    print(f'\n❌ FAIL: {strategy_id} not found')
