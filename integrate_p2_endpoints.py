#!/usr/bin/env python3
"""
Script d'intégration P2 dans api/main.py
"""

import re

MAIN_PY_PATH = "/opt/smartorder-pro/api/main.py"

# Lire fichier actuel
with open(MAIN_PY_PATH, 'r') as f:
    content = f.read()

# 1. Ajouter imports si manquants
if 'from fastapi import' in content and 'Depends' not in content:
    content = content.replace(
        'from fastapi import FastAPI, HTTPException',
        'from fastapi import FastAPI, HTTPException, Depends, Header'
    )
    print("✅ Imports Depends et Header ajoutés")

if 'from pydantic import BaseModel' not in content:
    # Ajouter après les imports fastapi
    content = content.replace(
        'from typing import Dict, Any',
        'from typing import Dict, Any, Optional\nfrom pydantic import BaseModel'
    )
    print("✅ Import BaseModel ajouté")

# 2. Ajouter le code P2 avant la dernière ligne
p2_code = '''

# ============================================================================
# P2 ENDPOINTS - Config Management (v2.1-P2)
# ============================================================================

# Token security
API_TOKEN = os.getenv("SMARTORDER_API_TOKEN", "dev_token_12345")

def verify_token(authorization: Optional[str] = Header(None)):
    """Vérifier Bearer token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    if parts[1] != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True

# === WALLET ENDPOINTS ===

PAPER_WALLET_FILE = f"{CONFIG_DIR}/paper_wallet.json"

@app.get("/api/wallet-p2")
async def get_paper_wallet(authorized: bool = Depends(verify_token)):
    """GET /api/wallet-p2 - Retourne l'état du paper wallet"""
    try:
        wallet = load_json(PAPER_WALLET_FILE, {
            "balance_usdt": 10000.0,
            "equity_usdt": 10000.0,
            "unrealized_pnl_usdt": 0.0,
            "realized_pnl_usdt": 0.0,
            "updated_at": datetime.now().isoformat()
        })
        return wallet
    except Exception as e:
        logger.error(f"Error loading wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class WalletReset(BaseModel):
    balance_usdt: Optional[float] = 10000.0

@app.post("/api/wallet-p2")
async def reset_paper_wallet(wallet_reset: WalletReset, authorized: bool = Depends(verify_token)):
    """POST /api/wallet-p2 - Reset le paper wallet"""
    try:
        wallet = {
            "balance_usdt": wallet_reset.balance_usdt,
            "equity_usdt": wallet_reset.balance_usdt,
            "unrealized_pnl_usdt": 0.0,
            "realized_pnl_usdt": 0.0,
            "updated_at": datetime.now().isoformat()
        }
        save_json(PAPER_WALLET_FILE, wallet)
        logger.info(f"Wallet reset to {wallet_reset.balance_usdt} USDT")
        return {"status": "wallet_reset", "wallet": wallet}
    except Exception as e:
        logger.error(f"Error resetting wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === RISK CONFIG ENDPOINTS ===

RISK_CONFIG_FILE = f"{CONFIG_DIR}/risk_config.json"

@app.get("/api/risk-config")
async def get_risk_config(authorized: bool = Depends(verify_token)):
    """GET /api/risk-config - Retourne la configuration Risk Management"""
    try:
        risk_config = load_json(RISK_CONFIG_FILE, {
            "max_position_size_usdt": 1000,
            "stop_loss_pct": 2.0,
            "take_profit_pct": 3.0,
            "max_open_trades": 5,
            "max_daily_loss_usdt": 100
        })
        return risk_config
    except Exception as e:
        logger.error(f"Error loading risk config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RiskConfig(BaseModel):
    max_position_size_usdt: float
    stop_loss_pct: float
    take_profit_pct: float
    max_open_trades: Optional[int] = 5
    max_daily_loss_usdt: Optional[float] = 100

@app.post("/api/risk-config")
async def update_risk_config(risk_config: RiskConfig, authorized: bool = Depends(verify_token)):
    """POST /api/risk-config - Met à jour la configuration Risk Management"""
    try:
        config_dict = risk_config.dict()
        save_json(RISK_CONFIG_FILE, config_dict)
        logger.info(f"Risk config updated: {config_dict}")
        return {"status": "risk_config_updated", "config": config_dict}
    except Exception as e:
        logger.error(f"Error updating risk config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === WATCHLIST ENDPOINTS ===

WATCHLIST_FILE = f"{CONFIG_DIR}/watchlist.json"

@app.get("/api/watchlist")
async def get_watchlist(authorized: bool = Depends(verify_token)):
    """GET /api/watchlist - Retourne la liste des paires surveillées"""
    try:
        watchlist = load_json(WATCHLIST_FILE, {
            "pairs": ["BTC/USDT", "ETH/USDT"],
            "updated_at": datetime.now().isoformat()
        })
        return watchlist
    except Exception as e:
        logger.error(f"Error loading watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class Watchlist(BaseModel):
    pairs: list

@app.post("/api/watchlist")
async def update_watchlist(watchlist: Watchlist, authorized: bool = Depends(verify_token)):
    """POST /api/watchlist - Met à jour la watchlist"""
    try:
        for pair in watchlist.pairs:
            if '/' not in pair:
                raise HTTPException(status_code=400, detail=f"Invalid pair format: {pair}")
        
        watchlist_dict = {
            "pairs": watchlist.pairs,
            "updated_at": datetime.now().isoformat()
        }
        save_json(WATCHLIST_FILE, watchlist_dict)
        logger.info(f"Watchlist updated: {watchlist.pairs}")
        return {"status": "watchlist_updated", "watchlist": watchlist_dict}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# END P2 ENDPOINTS
'''

# Insérer avant la dernière ligne de log
lines = content.split('\n')
insert_pos = len(lines) - 2  # Avant dernière ligne

lines.insert(insert_pos, p2_code)
content = '\n'.join(lines)

# Sauvegarder
with open(MAIN_PY_PATH, 'w') as f:
    f.write(content)

print("✅ Endpoints P2 intégrés dans api/main.py")
print("📄 Backup disponible: api/main.py.backup_P2_*")
print("\n🔄 Redémarrez l'API pour appliquer les changements")
