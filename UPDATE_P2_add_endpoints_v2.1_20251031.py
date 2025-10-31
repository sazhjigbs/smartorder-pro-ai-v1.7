#!/usr/bin/env python3
"""
UPDATE P2: Ajout Endpoints API v2.1
Date: 2025-10-31
Version: v2.1-P2

OBJECTIF:
- Ajouter GET/POST /api/wallet dans FastAPI existante
- Ajouter GET/POST /api/risk-config
- Ajouter GET/POST /api/watchlist
- Sécurité Bearer token depuis config/web.env
- Lecture/écriture fichiers config réels

DoD:
- GET renvoie état réel fichiers
- POST modifie fichiers
- Protection Bearer token
- Documentation complète
"""

# Code à ajouter dans /opt/smartorder-pro/api/main.py

ENDPOINTS_CODE = '''
# ============================================================================
# P2 ENDPOINTS - Config Management
# ============================================================================

from fastapi import Header, HTTPException
from pydantic import BaseModel
from typing import Optional

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

@app.get("/api/wallet")
async def get_paper_wallet(authorized: bool = Depends(verify_token)):
    """
    GET /api/wallet
    Retourne l'état du paper wallet
    """
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

@app.post("/api/wallet")
async def reset_paper_wallet(
    wallet_reset: WalletReset,
    authorized: bool = Depends(verify_token)
):
    """
    POST /api/wallet
    Reset le paper wallet
    Body: {"balance_usdt": 10000.0}
    """
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
    """
    GET /api/risk-config
    Retourne la configuration Risk Management
    """
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
async def update_risk_config(
    risk_config: RiskConfig,
    authorized: bool = Depends(verify_token)
):
    """
    POST /api/risk-config
    Met à jour la configuration Risk Management
    Body: {"max_position_size_usdt": 1000, "stop_loss_pct": 2.0, ...}
    """
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
    """
    GET /api/watchlist
    Retourne la liste des paires surveillées
    """
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
async def update_watchlist(
    watchlist: Watchlist,
    authorized: bool = Depends(verify_token)
):
    """
    POST /api/watchlist
    Met à jour la watchlist
    Body: {"pairs": ["BTC/USDT", "ETH/USDT", "SOL/USDT"]}
    """
    try:
        # Validation format
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

print("""
================================================================================
UPDATE P2: Ajout Endpoints FastAPI
================================================================================

Code à ajouter dans /opt/smartorder-pro/api/main.py

IMPORTS À AJOUTER (après les imports existants):
from fastapi import Depends

ENDPOINTS À AJOUTER (avant la fin du fichier):
- GET/POST /api/wallet
- GET/POST /api/risk-config
- GET/POST /api/watchlist

MÉTHODE:
1. Ouvrir api/main.py
2. Ajouter "from fastapi import Depends" dans les imports
3. Copier le code des endpoints avant la fin du fichier
4. Redémarrer l'API: systemctl restart smartorder-api (ou kill + relaunch)

TESTS:
curl -H "Authorization: Bearer dev_token_12345" http://localhost:8000/api/wallet
curl -H "Authorization: Bearer dev_token_12345" http://localhost:8000/api/risk-config
curl -H "Authorization: Bearer dev_token_12345" http://localhost:8000/api/watchlist

================================================================================
""")

# Sauvegarder le code dans un fichier pour intégration
with open("/tmp/p2_endpoints.txt", "w") as f:
    f.write(ENDPOINTS_CODE)

print("✅ Code endpoints sauvegardé dans /tmp/p2_endpoints.txt")
print("📝 Prêt pour intégration manuelle ou automatique")
