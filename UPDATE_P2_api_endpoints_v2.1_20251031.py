#!/usr/bin/env python3
"""
UPDATE P2: API REST Endpoints v2.1
Date: 2025-10-31
Version: v2.1-P2

OBJECTIF:
- Exposition REST pour manipulation état réel
- GET/POST /api/wallet, /api/risk-config, /api/watchlist
- Sécurité Bearer token
- Synchronisation avec fichiers config

DoD:
- GET renvoie état réel fichiers
- POST modifie fichiers + recharge config
- 401 si token absent/incorrect
- Documentation API complète
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import json
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Configuration
CONFIG_DIR = Path("/opt/smartorder-pro/config")
WATCHLIST_FILE = CONFIG_DIR / "watchlist.json"
RISK_CONFIG_FILE = CONFIG_DIR / "risk_config.json"
PAPER_WALLET_FILE = CONFIG_DIR / "paper_wallet.json"

# Token security
API_TOKEN = os.getenv("SMARTORDER_API_TOKEN", "dev_token_12345")

def require_token(f):
    """Decorator pour vérifier token Bearer"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid Authorization header format"}), 401
        
        token = parts[1]
        if token != API_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated

# ============================================================================
# WALLET ENDPOINTS
# ============================================================================

@app.route('/api/wallet', methods=['GET'])
@require_token
def get_wallet():
    """
    GET /api/wallet
    Retourne l'état actuel du paper wallet
    """
    try:
        with open(PAPER_WALLET_FILE, 'r') as f:
            wallet = json.load(f)
        return jsonify(wallet), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet', methods=['POST'])
@require_token
def reset_wallet():
    """
    POST /api/wallet
    Reset ou initialise le wallet
    Body: {"balance_usdt": 10000.0} (optionnel)
    """
    try:
        data = request.get_json() or {}
        initial_balance = data.get('balance_usdt', 10000.0)
        
        wallet = {
            "balance_usdt": initial_balance,
            "equity_usdt": initial_balance,
            "unrealized_pnl_usdt": 0.0,
            "realized_pnl_usdt": 0.0,
            "updated_at": datetime.now().isoformat()
        }
        
        with open(PAPER_WALLET_FILE, 'w') as f:
            json.dump(wallet, f, indent=2)
        
        return jsonify({"status": "wallet_reset", "wallet": wallet}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# RISK CONFIG ENDPOINTS
# ============================================================================

@app.route('/api/risk-config', methods=['GET'])
@require_token
def get_risk_config():
    """
    GET /api/risk-config
    Retourne la configuration risk management
    """
    try:
        with open(RISK_CONFIG_FILE, 'r') as f:
            risk_config = json.load(f)
        return jsonify(risk_config), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk-config', methods=['POST'])
@require_token
def update_risk_config():
    """
    POST /api/risk-config
    Met à jour la configuration risk
    Body: {"max_position_size_usdt": 1000, "stop_loss_pct": 2.0, ...}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Empty body"}), 400
        
        # Validation des champs requis
        required_fields = ["max_position_size_usdt", "stop_loss_pct", "take_profit_pct"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Sauvegarder config
        with open(RISK_CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"status": "risk_config_updated", "config": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# WATCHLIST ENDPOINTS
# ============================================================================

@app.route('/api/watchlist', methods=['GET'])
@require_token
def get_watchlist():
    """
    GET /api/watchlist
    Retourne la liste des paires surveillées
    """
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            watchlist = json.load(f)
        return jsonify(watchlist), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/watchlist', methods=['POST'])
@require_token
def update_watchlist():
    """
    POST /api/watchlist
    Met à jour la watchlist
    Body: {"pairs": ["BTC/USDT", "ETH/USDT", "SOL/USDT"]}
    """
    try:
        data = request.get_json()
        
        if not data or 'pairs' not in data:
            return jsonify({"error": "Missing 'pairs' field"}), 400
        
        if not isinstance(data['pairs'], list):
            return jsonify({"error": "'pairs' must be a list"}), 400
        
        # Validation format pairs
        for pair in data['pairs']:
            if '/' not in pair:
                return jsonify({"error": f"Invalid pair format: {pair}"}), 400
        
        watchlist = {
            "pairs": data['pairs'],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(watchlist, f, indent=2)
        
        return jsonify({"status": "watchlist_updated", "watchlist": watchlist}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    GET /api/health
    Health check endpoint (pas de token requis)
    """
    return jsonify({
        "status": "healthy",
        "version": "v2.1-P2",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def root():
    """
    GET /
    Root endpoint avec documentation basique
    """
    return jsonify({
        "name": "SmartOrder PRO API",
        "version": "v2.1-P2",
        "endpoints": {
            "/api/health": "Health check",
            "/api/wallet": "GET/POST wallet",
            "/api/risk-config": "GET/POST risk management config",
            "/api/watchlist": "GET/POST trading pairs watchlist"
        },
        "authentication": "Bearer token required (except /api/health)"
    }), 200

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SmartOrder PRO API v2.1-P2")
    print("=" * 60)
    print(f"API Token: {API_TOKEN[:10]}...")
    print("Endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/wallet")
    print("  POST /api/wallet")
    print("  GET  /api/risk-config")
    print("  POST /api/risk-config")
    print("  GET  /api/watchlist")
    print("  POST /api/watchlist")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=False)
