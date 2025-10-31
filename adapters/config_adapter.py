"""
SmartOrder PRO AI - Config Adapter Module
==========================================
Adaptateurs bidirectionnels pour assurer compatibilité entre formats v1 et v2
des fichiers de configuration.

Fonctionnalités:
- Détection automatique du format (v1 legacy ou v2 standard)
- Conversion transparente en mémoire
- Sauvegarde automatique au format v2
- Traçabilité complète via logs

Version: v2.1-P2P3-adapter
Date: 2025-10-31
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

CONFIG_DIR = Path("/opt/smartorder-pro/config")
RISK_CONFIG_PATH = CONFIG_DIR / "risk_config.json"
WATCHLIST_PATH = CONFIG_DIR / "watchlist.json"
WALLET_PATH = CONFIG_DIR / "paper_wallet.json"
TRADING_MODES_PATH = CONFIG_DIR / "trading_modes.json"


# ============================================================================
# RISK CONFIG ADAPTER
# ============================================================================

def read_risk_config() -> Dict[str, Any]:
    """
    Lit risk_config.json et retourne le format v2 standard.
    Détecte automatiquement si le format est v1 ou v2.
    """
    try:
        with open(RISK_CONFIG_PATH, 'r') as f:
            data = json.load(f)
        
        # Détection du format
        if "max_position_size_usdt" in data:
            # Format v1 (legacy) - conversion nécessaire
            logger.info("[ADAPTER] risk_config.json détecté en format v1, conversion en v2")
            standardized = {
                "max_allocation_per_trade": data.get("max_position_size_usdt", 1000),
                "max_risk_per_trade": data.get("max_position_size_usdt", 1000) / 10000 * 100,  # Calcul %
                "stop_loss_percent": data.get("stop_loss_pct", 2.0),
                "take_profit_percent": data.get("take_profit_pct", 3.0),
                "max_open_trades": data.get("max_open_trades", 5),
                "max_daily_loss_usdt": data.get("max_daily_loss_usdt", 100),
                "risk_mode": "conservative"
            }
            # Sauvegarde automatique au format v2
            write_risk_config(standardized)
            return standardized
        
        elif "max_allocation_per_trade" in data:
            # Format v2 (standard) - déjà compatible
            logger.info("[ADAPTER] risk_config.json déjà en format v2 standard")
            return data
        
        else:
            # Format inconnu - utiliser valeurs par défaut
            logger.warning("[ADAPTER] Format risk_config.json inconnu, utilisation valeurs par défaut")
            default_config = {
                "max_allocation_per_trade": 1000,
                "max_risk_per_trade": 10,
                "stop_loss_percent": 2.0,
                "take_profit_percent": 3.0,
                "max_open_trades": 5,
                "max_daily_loss_usdt": 100,
                "risk_mode": "conservative"
            }
            write_risk_config(default_config)
            return default_config
    
    except FileNotFoundError:
        logger.error(f"[ADAPTER] Fichier {RISK_CONFIG_PATH} introuvable")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[ADAPTER] Erreur parsing risk_config.json: {e}")
        raise


def write_risk_config(data: Dict[str, Any]) -> None:
    """
    Écrit risk_config.json toujours au format v2 standard.
    """
    try:
        # Format v2 standard
        standardized = {
            "max_allocation_per_trade": data.get("max_allocation_per_trade", 1000),
            "max_risk_per_trade": data.get("max_risk_per_trade", 10),
            "stop_loss_percent": data.get("stop_loss_percent", 2.0),
            "take_profit_percent": data.get("take_profit_percent", 3.0),
            "max_open_trades": data.get("max_open_trades", 5),
            "max_daily_loss_usdt": data.get("max_daily_loss_usdt", 100),
            "risk_mode": data.get("risk_mode", "conservative"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(RISK_CONFIG_PATH, 'w') as f:
            json.dump(standardized, f, indent=2)
        
        logger.info(f"[ADAPTER] risk_config.json sauvegardé en format v2 à {RISK_CONFIG_PATH}")
    
    except Exception as e:
        logger.error(f"[ADAPTER] Erreur écriture risk_config.json: {e}")
        raise


# ============================================================================
# WATCHLIST ADAPTER
# ============================================================================

def read_watchlist() -> List[Dict[str, Any]]:
    """
    Lit watchlist.json et retourne le format v2 standard.
    Format v2: [{"exchange": "binance", "symbol": "BTC/USDT", "active": true}, ...]
    """
    try:
        with open(WATCHLIST_PATH, 'r') as f:
            data = json.load(f)
        
        # Détection du format
        if "pairs" in data and isinstance(data["pairs"], list):
            # Format v1 (legacy) - liste simple de symboles
            if len(data["pairs"]) > 0 and isinstance(data["pairs"][0], str):
                logger.info("[ADAPTER] watchlist.json détecté en format v1, conversion en v2")
                standardized = [
                    {
                        "exchange": "binance",  # Exchange par défaut
                        "symbol": symbol,
                        "active": True
                    }
                    for symbol in data["pairs"]
                ]
                # Sauvegarde automatique au format v2
                write_watchlist(standardized)
                return standardized
            
            # Format v2 mais sous clé "pairs"
            elif len(data["pairs"]) > 0 and isinstance(data["pairs"][0], dict):
                logger.info("[ADAPTER] watchlist.json en format v2 sous clé 'pairs'")
                write_watchlist(data["pairs"])  # Normaliser sans la clé "pairs"
                return data["pairs"]
        
        elif isinstance(data, list):
            # Format v2 (standard) - liste d'objets
            if len(data) > 0 and isinstance(data[0], dict) and "symbol" in data[0]:
                logger.info("[ADAPTER] watchlist.json déjà en format v2 standard")
                return data
        
        # Format inconnu ou vide - retourner liste vide
        logger.warning("[ADAPTER] Format watchlist.json inconnu ou vide, retour liste vide")
        return []
    
    except FileNotFoundError:
        logger.error(f"[ADAPTER] Fichier {WATCHLIST_PATH} introuvable")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"[ADAPTER] Erreur parsing watchlist.json: {e}")
        return []


def write_watchlist(pairs: List[Dict[str, Any]]) -> None:
    """
    Écrit watchlist.json toujours au format v2 standard.
    Format v2: [{"exchange": "binance", "symbol": "BTC/USDT", "active": true}, ...]
    """
    try:
        # Standardisation format v2
        standardized = []
        for pair in pairs:
            if isinstance(pair, dict):
                standardized.append({
                    "exchange": pair.get("exchange", "binance"),
                    "symbol": pair.get("symbol", "BTC/USDT"),
                    "active": pair.get("active", True)
                })
        
        # Ajout métadonnées
        output = {
            "pairs": standardized,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(WATCHLIST_PATH, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"[ADAPTER] watchlist.json sauvegardé en format v2 à {WATCHLIST_PATH}")
    
    except Exception as e:
        logger.error(f"[ADAPTER] Erreur écriture watchlist.json: {e}")
        raise


# ============================================================================
# WALLET ADAPTER
# ============================================================================

def read_wallet() -> Dict[str, Any]:
    """
    Lit paper_wallet.json et retourne le format v2 standard API.
    Format v2 API: {"USDT": float, "total_invested": float, "total_pnl": float, "total_trades": int}
    """
    try:
        with open(WALLET_PATH, 'r') as f:
            data = json.load(f)
        
        # Détection du format
        if "balance_usdt" in data:
            # Format v1 (legacy) - conversion nécessaire
            logger.info("[ADAPTER] paper_wallet.json détecté en format v1, conversion en v2")
            
            # Calcul des métriques v2
            balance = data.get("balance_usdt", 10000.0)
            realized_pnl = data.get("realized_pnl_usdt", 0.0)
            initial_balance = 10000.0  # Balance initiale par défaut
            
            standardized = {
                "USDT": balance,
                "total_invested": initial_balance - balance + realized_pnl,
                "total_pnl": realized_pnl,
                "total_trades": 0,  # Non disponible en v1
                "updated_at": data.get("updated_at", datetime.utcnow().isoformat())
            }
            
            return standardized
        
        elif "USDT" in data:
            # Format v2 (standard API) - déjà compatible
            logger.info("[ADAPTER] paper_wallet.json déjà en format v2 standard API")
            return data
        
        else:
            # Format inconnu - valeurs par défaut
            logger.warning("[ADAPTER] Format paper_wallet.json inconnu, utilisation valeurs par défaut")
            return {
                "USDT": 10000.0,
                "total_invested": 0.0,
                "total_pnl": 0.0,
                "total_trades": 0,
                "updated_at": datetime.utcnow().isoformat()
            }
    
    except FileNotFoundError:
        logger.error(f"[ADAPTER] Fichier {WALLET_PATH} introuvable")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[ADAPTER] Erreur parsing paper_wallet.json: {e}")
        raise


def write_wallet(data: Dict[str, Any]) -> None:
    """
    Écrit paper_wallet.json en format v1 (bot) + métadonnées v2 (API).
    Garde rétrocompatibilité avec le bot existant.
    """
    try:
        # Format hybride v1+v2 pour compatibilité
        usdt_balance = data.get("USDT", 10000.0)
        total_pnl = data.get("total_pnl", 0.0)
        
        wallet_data = {
            # Format v1 (pour le bot)
            "balance_usdt": usdt_balance,
            "equity_usdt": usdt_balance,
            "unrealized_pnl_usdt": 0.0,
            "realized_pnl_usdt": total_pnl,
            
            # Métadonnées v2 (pour l'API)
            "total_invested": data.get("total_invested", 0.0),
            "total_trades": data.get("total_trades", 0),
            
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(WALLET_PATH, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        logger.info(f"[ADAPTER] paper_wallet.json sauvegardé en format hybride v1+v2 à {WALLET_PATH}")
    
    except Exception as e:
        logger.error(f"[ADAPTER] Erreur écriture paper_wallet.json: {e}")
        raise


# ============================================================================
# TRADING MODES ADAPTER (P4)
# ============================================================================

def read_trading_modes() -> Dict[str, Any]:
    """
    Lit trading_modes.json et retourne la configuration des modes et stratégies.
    Format v2: {current_mode, modes, strategies, ai_strategy_selector}
    """
    try:
        with open(TRADING_MODES_PATH, 'r') as f:
            data = json.load(f)
        
        # Vérifier format v2
        if "current_mode" in data and "strategies" in data:
            logger.info("[ADAPTER] trading_modes.json déjà en format v2")
            return data
        
        # Format par défaut si fichier corrompu
        logger.warning("[ADAPTER] trading_modes.json format inconnu, retour config par défaut")
        default_config = {
            "current_mode": "spot",
            "modes": {
                "spot": {"name": "Auto Spot AI", "enabled": True},
                "futures": {"name": "Auto Futures AI", "enabled": False},
                "hybrid": {"name": "Hybride", "enabled": False},
                "manual": {"name": "Manuel", "enabled": False}
            },
            "strategies": {"spot": [], "futures": [], "hybrid": []},
            "ai_strategy_selector": {"enabled": False},
            "updated_at": datetime.utcnow().isoformat()
        }
        write_trading_modes(default_config)
        return default_config
    
    except FileNotFoundError:
        logger.error(f"[ADAPTER] Fichier {TRADING_MODES_PATH} introuvable")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[ADAPTER] Erreur parsing trading_modes.json: {e}")
        raise


def write_trading_modes(data: Dict[str, Any]) -> None:
    """
    Écrit trading_modes.json toujours au format v2.
    """
    try:
        # S'assurer que les champs essentiels existent
        standardized = {
            "current_mode": data.get("current_mode", "spot"),
            "modes": data.get("modes", {}),
            "strategies": data.get("strategies", {}),
            "ai_strategy_selector": data.get("ai_strategy_selector", {"enabled": False}),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(TRADING_MODES_PATH, 'w') as f:
            json.dump(standardized, f, indent=2)
        
        logger.info(f"[ADAPTER] trading_modes.json sauvegardé en format v2 à {TRADING_MODES_PATH}")
    
    except Exception as e:
        logger.error(f"[ADAPTER] Erreur écriture trading_modes.json: {e}")
        raise


# ============================================================================
# DIAGNOSTIC MEMORY INTEGRATION
# ============================================================================

def log_conversion_to_memory(file_name: str, old_format: str, new_format: str) -> None:
    """
    Journalise les conversions de format dans le diagnostic mémoire.
    """
    try:
        diagnostic_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "config_format_conversion",
            "file": file_name,
            "old_format": old_format,
            "new_format": new_format,
            "adapter_version": "v2.1-P2P3"
        }
        
        log_path = Path("/opt/smartorder-pro/logs/diagnostic_memory.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(diagnostic_log) + '\n')
        
        logger.info(f"[ADAPTER] Conversion journalisée dans diagnostic_memory.jsonl")
    
    except Exception as e:
        logger.warning(f"[ADAPTER] Impossible de journaliser la conversion: {e}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def migrate_all_configs_to_v2() -> None:
    """
    Force la migration de tous les fichiers config vers le format v2.
    Utile pour migration complète du système.
    """
    logger.info("[ADAPTER] === Début migration complète vers format v2 ===")
    
    try:
        # Migration risk_config
        risk = read_risk_config()
        write_risk_config(risk)
        logger.info("[ADAPTER] ✅ risk_config.json migré")
        
        # Migration watchlist
        watchlist = read_watchlist()
        write_watchlist(watchlist)
        logger.info("[ADAPTER] ✅ watchlist.json migré")
        
        # Note: wallet garde format hybride pour compatibilité bot
        logger.info("[ADAPTER] ℹ️  paper_wallet.json reste en format hybride v1+v2")
        
        logger.info("[ADAPTER] === Migration complète terminée ===")
    
    except Exception as e:
        logger.error(f"[ADAPTER] Erreur lors de la migration: {e}")
        raise


if __name__ == "__main__":
    # Test du module adapter
    logging.basicConfig(level=logging.INFO)
    
    print("=== Test Config Adapter v2.1 ===\n")
    
    print("1. Test read_risk_config():")
    risk = read_risk_config()
    print(json.dumps(risk, indent=2))
    
    print("\n2. Test read_watchlist():")
    watchlist = read_watchlist()
    print(json.dumps(watchlist, indent=2))
    
    print("\n3. Test read_wallet():")
    wallet = read_wallet()
    print(json.dumps(wallet, indent=2))
    
    print("\n=== Tests terminés ===")
