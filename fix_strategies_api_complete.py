#!/usr/bin/env python3
"""
CORRECTION COMPLETE API STRATEGIES + AUTO AI MODES
- Fix /api/strategies pour lire strategies.json (14 stratégies)
- Ajouter /api/modes/auto-select (Auto Spot AI / Auto Futures AI)
- Ajouter /api/modes/status
"""

import re

with open('/opt/smartorder-pro/api/main.py', 'r') as f:
    content = f.read()

# 1. REMPLACER ENDPOINT /api/strategies
old_strategies_pattern = r"@app\.get\('/api/strategies'\).*?(?=@app\.|# ===|$)"

new_strategies_code = """@app.get('/api/strategies')
def get_strategies(mode: Optional[str] = None):
    \"\"\"Retourne les 14 stratégies depuis strategies.json\"\"\"
    try:
        # Lire le fichier strategies.json (14 stratégies)
        data = read_json('strategies.json', {'strategies': []})
        strategies = data.get('strategies', [])
        
        # Filtrer par type si mode spécifié
        if mode:
            mode_upper = mode.upper()
            strategies = [s for s in strategies if s.get('type', '').upper() == mode_upper]
        
        # Enrichir avec info supplémentaire
        for s in strategies:
            # Ajouter mode en lowercase pour dashboard
            s['mode'] = s.get('type', 'SPOT').lower()
            # S'assurer que tous les champs requis existent
            if 'enabled' not in s:
                s['enabled'] = False
            if 'score' not in s:
                s['score'] = 50
        
        return {
            'strategies': strategies,
            'count': len(strategies),
            'total': len(data.get('strategies', [])),
            'mode_filter': mode or 'all'
        }
    except Exception as e:
        print(f"Error loading strategies: {e}")
        return {'strategies': [], 'count': 0, 'error': str(e)}

"""

content = re.sub(old_strategies_pattern, new_strategies_code, content, flags=re.DOTALL)

# 2. AJOUTER ENDPOINTS AUTO AI MODES (avant if __name__)
auto_ai_endpoints = """
# =====================
# AUTO AI MODES ENDPOINTS
# =====================

@app.post('/api/modes/auto-select')
async def auto_select_strategies(payload: dict):
    \"\"\"Sélection automatique des stratégies par IA (score ≥ threshold)\"\"\"
    try:
        mode_type = payload.get('type', 'spot').upper()  # SPOT, FUTURES, HYBRID
        threshold = payload.get('threshold', 70)
        
        # Lire strategies.json
        data = read_json('strategies.json', {'strategies': []})
        strategies = data.get('strategies', [])
        
        # Filtrer par type
        type_strategies = [s for s in strategies if s.get('type', '').upper() == mode_type]
        
        # Sélectionner celles avec score ≥ threshold
        selected = [s for s in type_strategies if s.get('score', 0) >= threshold]
        
        # Activer les stratégies sélectionnées, désactiver les autres
        for s in strategies:
            if s.get('type', '').upper() == mode_type:
                s['enabled'] = s in selected
        
        # Sauvegarder
        data['strategies'] = strategies
        data['last_update'] = datetime.now().isoformat()
        save_json('strategies.json', data)
        
        return {
            'status': 'success',
            'mode': mode_type,
            'threshold': threshold,
            'total': len(type_strategies),
            'selected': len(selected),
            'strategies': [s['id'] for s in selected]
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.get('/api/modes/status')
async def get_modes_status():
    \"\"\"État des modes Auto AI (Spot/Futures/Hybrid)\"\"\"
    try:
        data = read_json('strategies.json', {'strategies': []})
        strategies = data.get('strategies', [])
        
        spot_strategies = [s for s in strategies if s.get('type') == 'SPOT']
        futures_strategies = [s for s in strategies if s.get('type') == 'FUTURES']
        hybrid_strategies = [s for s in strategies if s.get('type') == 'HYBRID']
        
        return {
            'spot': {
                'total': len(spot_strategies),
                'enabled': len([s for s in spot_strategies if s.get('enabled')]),
                'avg_score': sum(s.get('score', 0) for s in spot_strategies) / len(spot_strategies) if spot_strategies else 0,
                'auto_mode': True  # TODO: lire depuis config
            },
            'futures': {
                'total': len(futures_strategies),
                'enabled': len([s for s in futures_strategies if s.get('enabled')]),
                'avg_score': sum(s.get('score', 0) for s in futures_strategies) / len(futures_strategies) if futures_strategies else 0,
                'auto_mode': True
            },
            'hybrid': {
                'total': len(hybrid_strategies),
                'enabled': len([s for s in hybrid_strategies if s.get('enabled')]),
                'avg_score': sum(s.get('score', 0) for s in hybrid_strategies) / len(hybrid_strategies) if hybrid_strategies else 0,
                'auto_mode': True
            }
        }
    except Exception as e:
        return {'error': str(e)}

@app.post('/api/strategies/bulk-toggle')
async def bulk_toggle_strategies(payload: dict):
    \"\"\"Activer/désactiver plusieurs stratégies en masse\"\"\"
    try:
        strategy_ids = payload.get('strategies', [])
        action = payload.get('action', 'enable')  # enable/disable
        
        data = read_json('strategies.json', {'strategies': []})
        strategies = data.get('strategies', [])
        
        modified = 0
        for s in strategies:
            if s.get('id') in strategy_ids:
                s['enabled'] = (action == 'enable')
                modified += 1
        
        data['strategies'] = strategies
        data['last_update'] = datetime.now().isoformat()
        save_json('strategies.json', data)
        
        return {
            'status': 'success',
            'modified': modified,
            'action': action
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

"""

# Ajouter avant if __name__
if "if __name__ == '__main__':" in content:
    content = content.replace(
        "if __name__ == '__main__':",
        auto_ai_endpoints + "\nif __name__ == '__main__':"
    )

# 3. AJOUTER FONCTION save_json SI MANQUANTE
if 'def save_json' not in content:
    save_json_func = """
def save_json(filename, data):
    \"\"\"Save JSON to config file\"\"\"
    filepath = CONFIG_PATH / filename
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

"""
    # Ajouter après read_json
    content = content.replace(
        "def read_json(",
        save_json_func + "\ndef read_json("
    )

# Sauvegarder
with open('/opt/smartorder-pro/api/main.py', 'w') as f:
    f.write(content)

print('✅ API Strategies corrigée')
print('   - /api/strategies lit maintenant strategies.json (14 stratégies)')
print('   - /api/modes/auto-select ajouté (Auto AI selection)')
print('   - /api/modes/status ajouté (État modes)')
print('   - /api/strategies/bulk-toggle ajouté (Toggle masse)')
