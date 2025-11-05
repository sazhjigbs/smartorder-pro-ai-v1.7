import sys
sys.path.insert(0, '/opt/smartorder-pro')

import json
from pathlib import Path

CONFIG_PATH = Path('/opt/smartorder-pro/config')

def test_toggle():
    """Test manuel du toggle"""
    strategy_id = 'grid_trading'
    
    # Lire fichier
    with open(CONFIG_PATH / 'trading_modes.json') as f:
        data = json.load(f)
    
    print(f"Data type: {type(data)}")
    print(f"Has strategies: {'strategies' in data}")
    print(f"Strategies type: {type(data.get('strategies'))}")
    
    updated = False
    new_state = None
    
    for mode in ['spot', 'futures', 'hybrid']:
        print(f"\nChecking mode: {mode}")
        mode_strategies = data.get('strategies', {}).get(mode, [])
        print(f"  Mode strategies type: {type(mode_strategies)}")
        print(f"  Count: {len(mode_strategies) if isinstance(mode_strategies, list) else 'N/A'}")
        
        if not isinstance(mode_strategies, list):
            print(f"  SKIP: not a list")
            continue
        
        for i, strat in enumerate(mode_strategies):
            strat_id = strat.get('id', strat.get('label', 'unknown'))
            print(f"    [{i}] {strat_id}")
            
            if strat_id == strategy_id:
                print(f"    FOUND! Current enabled: {strat.get('enabled')}")
                strat['enabled'] = not strat.get('enabled', False)
                new_state = strat['enabled']
                print(f"    New state: {new_state}")
                updated = True
                break
        
        if updated:
            break
    
    if updated:
        print(f"\n✅ SUCCESS: {strategy_id} toggled to {new_state}")
        # Écrire
        with open(CONFIG_PATH / 'trading_modes.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("File written successfully")
    else:
        print(f"\n❌ FAIL: Strategy {strategy_id} not found")

if __name__ == '__main__':
    test_toggle()
