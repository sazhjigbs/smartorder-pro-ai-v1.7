#!/usr/bin/env python3
"""
API Flask pour Dashboard SmartOrder PRO AI v2.1
Gestion persistante des stratégies, exchanges, modes et données temps réel
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

CONFIG_DIR = Path("/opt/smartorder-pro/config")
CONFIG_DIR.mkdir(exist_ok=True)

# Fichiers de configuration
STRATEGIES_FILE = CONFIG_DIR / "strategies_state.json"
EXCHANGES_FILE = CONFIG_DIR / "exchanges_state.json"
DASHBOARD_SETTINGS_FILE = CONFIG_DIR / "dashboard_settings.json"
PNL_FILE = CONFIG_DIR / "pnl_tracker.json"
WALLET_FILE = CONFIG_DIR / "paper_wallet.json"
SIGNALS_FILE = CONFIG_DIR / "last_signals.json"
POSITIONS_FILE = CONFIG_DIR / "positions.json"

# Helper functions
def load_json(filepath, default=None):
    """Charge un fichier JSON ou retourne default"""
    try:
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except:
        pass
    return default or {}

def save_json(filepath, data):
    """Sauvegarde dans un fichier JSON"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

# =============================================================================
# ROUTES - STRATÉGIES
# =============================================================================

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Récupère l'état de toutes les stratégies"""
    data = load_json(STRATEGIES_FILE, {
        "strategies": [],
        "auto_mode": {"spot": False, "futures": False}
    })
    return jsonify(data)

@app.route('/api/strategies/toggle', methods=['POST'])
def toggle_strategy():
    """Toggle une stratégie ON/OFF avec persistance"""
    strategy_id = request.json.get('strategy_id')
    
    if not strategy_id:
        return jsonify({"error": "strategy_id required"}), 400
    
    # Charger l'état actuel
    data = load_json(STRATEGIES_FILE, {"strategies": []})
    
    # Trouver et toggler la stratégie
    found = False
    for strat in data.get('strategies', []):
        if strat['id'] == strategy_id:
            strat['enabled'] = not strat.get('enabled', False)
            found = True
            break
    
    if not found:
        return jsonify({"error": "Strategy not found"}), 404
    
    # Sauvegarder
    data['last_update'] = datetime.now().isoformat()
    if save_json(STRATEGIES_FILE, data):
        return jsonify({"success": True, "strategies": data['strategies']})
    else:
        return jsonify({"error": "Save failed"}), 500

@app.route('/api/strategies/auto', methods=['POST'])
def set_auto_mode():
    """Active/désactive le mode Auto Spot/Futures"""
    mode = request.json.get('mode')  # 'spot' ou 'futures'
    enabled = request.json.get('enabled', False)
    
    if mode not in ['spot', 'futures']:
        return jsonify({"error": "Invalid mode"}), 400
    
    data = load_json(STRATEGIES_FILE, {"auto_mode": {}})
    
    if 'auto_mode' not in data:
        data['auto_mode'] = {}
    
    data['auto_mode'][mode] = enabled
    data['last_update'] = datetime.now().isoformat()
    
    if save_json(STRATEGIES_FILE, data):
        return jsonify({"success": True, "auto_mode": data['auto_mode']})
    else:
        return jsonify({"error": "Save failed"}), 500

# =============================================================================
# ROUTES - EXCHANGES
# =============================================================================

@app.route('/api/exchanges', methods=['GET'])
def get_exchanges():
    """Récupère l'état des exchanges"""
    data = load_json(EXCHANGES_FILE, {"exchanges": []})
    return jsonify(data)

@app.route('/api/exchanges/toggle', methods=['POST'])
def toggle_exchange():
    """Toggle un exchange ON/OFF avec persistance"""
    exchange_id = request.json.get('exchange_id')
    
    if not exchange_id:
        return jsonify({"error": "exchange_id required"}), 400
    
    data = load_json(EXCHANGES_FILE, {"exchanges": []})
    
    found = False
    for exchange in data.get('exchanges', []):
        if exchange['id'] == exchange_id:
            exchange['enabled'] = not exchange.get('enabled', False)
            found = True
            break
    
    if not found:
        return jsonify({"error": "Exchange not found"}), 404
    
    data['last_update'] = datetime.now().isoformat()
    
    if save_json(EXCHANGES_FILE, data):
        return jsonify({"success": True, "exchanges": data['exchanges']})
    else:
        return jsonify({"error": "Save failed"}), 500

# =============================================================================
# ROUTES - DONNÉES TEMPS RÉEL
# =============================================================================

@app.route('/api/pnl', methods=['GET'])
def get_pnl():
    """Récupère les données PnL"""
    data = load_json(PNL_FILE, {
        "total_pnl": 0,
        "daily_pnl": 0,
        "trades_count": 0,
        "win_rate": 0
    })
    return jsonify(data)

@app.route('/api/wallet', methods=['GET'])
def get_wallet():
    """Récupère le solde du portefeuille"""
    data = load_json(WALLET_FILE, {
        "balance_usdt": 10000,
        "total_pnl": 0,
        "open_positions": 0
    })
    return jsonify(data)

@app.route('/api/signals/last', methods=['GET'])
def get_last_signals():
    """Récupère les derniers signaux techniques"""
    data = load_json(SIGNALS_FILE, {})
    return jsonify(data)

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Récupère les positions ouvertes"""
    data = load_json(POSITIONS_FILE, {"positions": []})
    return jsonify(data)

# =============================================================================
# ROUTES - DASHBOARD SETTINGS
# =============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Récupère les paramètres du dashboard"""
    data = load_json(DASHBOARD_SETTINGS_FILE, {
        "theme": "dark",
        "refresh_interval": 5000,
        "show_indicators": True
    })
    return jsonify(data)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Met à jour les paramètres du dashboard"""
    data = request.json
    data['last_update'] = datetime.now().isoformat()
    
    if save_json(DASHBOARD_SETTINGS_FILE, data):
        return jsonify({"success": True, "settings": data})
    else:
        return jsonify({"error": "Save failed"}), 500

# =============================================================================
# ROUTES - EMERGENCY CONTROLS
# =============================================================================

@app.route('/api/emergency/stop', methods=['POST'])
def emergency_stop():
    """Arrêt d'urgence du trading"""
    # TODO: Implémenter la logique d'arrêt
    return jsonify({"success": True, "action": "STOPPED"})

@app.route('/api/emergency/pause', methods=['POST'])
def emergency_pause():
    """Pause du trading"""
    # TODO: Implémenter la logique de pause
    return jsonify({"success": True, "action": "PAUSED"})

@app.route('/api/emergency/resume', methods=['POST'])
def emergency_resume():
    """Reprise du trading"""
    # TODO: Implémenter la logique de reprise
    return jsonify({"success": True, "action": "RESUMED"})

# =============================================================================
# ROUTE - HEALTH CHECK
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check de l'API"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
