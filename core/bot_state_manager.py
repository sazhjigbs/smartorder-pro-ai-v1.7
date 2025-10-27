"""
🎮 Bot State Manager
Gestion centralisée de l'état du bot de trading
by MAIGA ABOUBACAR
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class TradingStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    EMERGENCY = "emergency"

class TradingMode(Enum):
    AUTO_SPOT = "auto_spot"
    AUTO_FUTURES = "auto_futures"
    MANUAL = "manual"
    HYBRID = "hybrid"

class BotStateManager:
    """Gestionnaire d'état du bot accessible par tous les services"""
    
    def __init__(self, state_file: str = "/opt/smartorder-pro/data/bot_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger ou créer l'état initial
        if not self.state_file.exists():
            self._create_initial_state()
    
    def _create_initial_state(self):
        """Crée l'état initial du bot"""
        initial_state = {
            "status": TradingStatus.STOPPED.value,
            "mode": TradingMode.MANUAL.value,
            "started_at": None,
            "stopped_at": None,
            "last_update": datetime.now().isoformat(),
            "pnl_today": 0.0,
            "trades_count": 0,
            "exchange": "bybit",
            "paper_trading": True,  # Sécurité : commence en paper trading
            "risk_level": "low",  # low, medium, high
            "max_position_size": 100.0,  # USDT
            "emergency_stop_active": False
        }
        self._write_state(initial_state)
    
    def _read_state(self) -> Dict[str, Any]:
        """Lit l'état actuel"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur lecture state: {e}")
            self._create_initial_state()
            return self._read_state()
    
    def _write_state(self, state: Dict[str, Any]):
        """Écrit l'état"""
        state["last_update"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    # ===========================================
    # CONTRÔLES PRINCIPAUX
    # ===========================================
    
    def start_trading(self, mode: str = "manual") -> Dict[str, Any]:
        """Démarre le trading"""
        state = self._read_state()
        
        if state["status"] == TradingStatus.RUNNING.value:
            return {"success": False, "message": "Trading already running"}
        
        state["status"] = TradingStatus.RUNNING.value
        state["mode"] = mode
        state["started_at"] = datetime.now().isoformat()
        state["stopped_at"] = None
        state["emergency_stop_active"] = False
        
        self._write_state(state)
        
        return {
            "success": True,
            "message": f"Trading started in {mode} mode",
            "state": state
        }
    
    def stop_trading(self) -> Dict[str, Any]:
        """Arrête le trading"""
        state = self._read_state()
        
        if state["status"] == TradingStatus.STOPPED.value:
            return {"success": False, "message": "Trading already stopped"}
        
        state["status"] = TradingStatus.STOPPED.value
        state["stopped_at"] = datetime.now().isoformat()
        
        self._write_state(state)
        
        return {
            "success": True,
            "message": "Trading stopped",
            "state": state
        }
    
    def pause_trading(self) -> Dict[str, Any]:
        """Met en pause le trading"""
        state = self._read_state()
        
        if state["status"] != TradingStatus.RUNNING.value:
            return {"success": False, "message": "Trading not running"}
        
        state["status"] = TradingStatus.PAUSED.value
        
        self._write_state(state)
        
        return {
            "success": True,
            "message": "Trading paused",
            "state": state
        }
    
    def resume_trading(self) -> Dict[str, Any]:
        """Reprend le trading"""
        state = self._read_state()
        
        if state["status"] != TradingStatus.PAUSED.value:
            return {"success": False, "message": "Trading not paused"}
        
        state["status"] = TradingStatus.RUNNING.value
        
        self._write_state(state)
        
        return {
            "success": True,
            "message": "Trading resumed",
            "state": state
        }
    
    def emergency_stop(self) -> Dict[str, Any]:
        """Arrêt d'urgence"""
        state = self._read_state()
        
        state["status"] = TradingStatus.EMERGENCY.value
        state["emergency_stop_active"] = True
        state["stopped_at"] = datetime.now().isoformat()
        
        self._write_state(state)
        
        return {
            "success": True,
            "message": "🚨 EMERGENCY STOP ACTIVATED",
            "state": state
        }
    
    # ===========================================
    # GETTERS / SETTERS
    # ===========================================
    
    def get_status(self) -> str:
        """Retourne le statut actuel"""
        return self._read_state()["status"]
    
    def is_trading_active(self) -> bool:
        """Vérifie si le trading est actif"""
        status = self.get_status()
        return status == TradingStatus.RUNNING.value
    
    def get_full_state(self) -> Dict[str, Any]:
        """Retourne l'état complet"""
        return self._read_state()
    
    def update_pnl(self, pnl: float):
        """Met à jour le PNL"""
        state = self._read_state()
        state["pnl_today"] = pnl
        self._write_state(state)
    
    def increment_trades(self):
        """Incrémente le compteur de trades"""
        state = self._read_state()
        state["trades_count"] += 1
        self._write_state(state)
    
    def set_mode(self, mode: str):
        """Change le mode de trading"""
        state = self._read_state()
        state["mode"] = mode
        self._write_state(state)
    
    def set_exchange(self, exchange: str):
        """Change l'exchange actif"""
        state = self._read_state()
        state["exchange"] = exchange
        self._write_state(state)
    
    def enable_paper_trading(self, enabled: bool = True):
        """Active/désactive le paper trading"""
        state = self._read_state()
        state["paper_trading"] = enabled
        self._write_state(state)
    
    def update_risk_params(self, risk_level: Optional[str] = None, 
                          max_position_size: Optional[float] = None):
        """Met à jour les paramètres de risque"""
        state = self._read_state()
        
        if risk_level:
            state["risk_level"] = risk_level
        if max_position_size:
            state["max_position_size"] = max_position_size
        
        self._write_state(state)
        
        return {
            "success": True,
            "risk_level": state["risk_level"],
            "max_position_size": state["max_position_size"]
        }

# Instance globale
_state_manager = None

def get_state_manager() -> BotStateManager:
    """Récupère l'instance du state manager (singleton)"""
    global _state_manager
    if _state_manager is None:
        _state_manager = BotStateManager()
    return _state_manager
