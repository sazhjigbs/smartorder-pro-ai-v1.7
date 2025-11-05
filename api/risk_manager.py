"""
SmartOrder PRO AI v2.4 - Risk Management AI Module
Dynamic Auto-Adaptive Risk System based on Market Reliability Score
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Config paths
CONFIG_DIR = Path(__file__).parent.parent / "config"
RISK_CONFIG = CONFIG_DIR / "risk.json"
PNL_TRACKER = CONFIG_DIR / "pnl_tracker.json"
SIGNALS_FILE = CONFIG_DIR / "last_signals.json"


class RiskMode:
    """Risk mode definitions with thresholds"""
    AGGRESSIVE = {
        "name": "AGGRESSIVE",
        "min_reliability": 80,
        "max_leverage": 3,
        "max_positions": 10,
        "stop_loss": 2.5,
        "take_profit": 5.0,
        "position_size": 1.5,
        "description": "High reliability - Aggressive trading"
    }
    
    BALANCED = {
        "name": "BALANCED",
        "min_reliability": 60,
        "max_leverage": 2,
        "max_positions": 6,
        "stop_loss": 2.0,
        "take_profit": 3.5,
        "position_size": 1.0,
        "description": "Moderate reliability - Balanced approach"
    }
    
    PREVENTIVE = {
        "name": "PREVENTIVE",
        "min_reliability": 40,
        "max_leverage": 1.5,
        "max_positions": 3,
        "stop_loss": 1.0,
        "take_profit": 2.0,
        "position_size": 0.7,
        "description": "Low reliability - Conservative trading"
    }
    
    DEFENSIVE = {
        "name": "DEFENSIVE",
        "min_reliability": 20,
        "max_leverage": 1.0,
        "max_positions": 2,
        "stop_loss": 0.8,
        "take_profit": 1.5,
        "position_size": 0.5,
        "description": "Very low reliability - Partial freeze"
    }
    
    SAFE_MODE = {
        "name": "SAFE_MODE",
        "min_reliability": 0,
        "max_leverage": 0,
        "max_positions": 0,
        "stop_loss": 0.5,
        "take_profit": 1.0,
        "position_size": 0.0,
        "description": "Critical - Trading stopped"
    }


class RiskManager:
    """Dynamic AI-powered Risk Management System"""
    
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.current_mode = "BALANCED"
        self.auto_mode = True
        self.risk_history = []
        self.initialize_config()
    
    def initialize_config(self):
        """Initialize risk configuration file"""
        if not RISK_CONFIG.exists():
            default_config = {
                "auto_mode": True,
                "current_mode": "BALANCED",
                "daily_loss_limit": 500,
                "max_drawdown_percent": 15,
                "emergency_stop_active": False,
                "last_update": datetime.now().isoformat(),
                "risk_history": []
            }
            self.save_config(default_config)
    
    def load_config(self) -> Dict:
        """Load risk configuration"""
        try:
            if RISK_CONFIG.exists():
                with open(RISK_CONFIG, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Risk config load error: {e}")
        return {}
    
    def save_config(self, config: Dict):
        """Save risk configuration"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(RISK_CONFIG, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Risk config save error: {e}")
    
    def load_json(self, filepath: Path) -> Dict:
        """Load JSON file safely"""
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def calculate_ai_confidence(self) -> float:
        """Get AI confidence from signals"""
        signals = self.load_json(SIGNALS_FILE)
        return signals.get("ai_confidence", 0.75)
    
    def calculate_volatility_score(self) -> float:
        """Calculate volatility score (inverse - low vol = high score)"""
        signals = self.load_json(SIGNALS_FILE)
        volatility = signals.get("volatility", "MEDIUM")
        
        vol_scores = {
            "LOW": 0.9,
            "MEDIUM": 0.7,
            "HIGH": 0.4,
            "EXTREME": 0.2
        }
        return vol_scores.get(volatility, 0.7)
    
    def calculate_regime_stability(self) -> float:
        """Calculate market regime stability score"""
        signals = self.load_json(SIGNALS_FILE)
        regime = signals.get("regime", "NEUTRAL")
        
        regime_scores = {
            "TRENDING_UP": 0.85,
            "TRENDING_DOWN": 0.75,
            "RANGING": 0.80,
            "NEUTRAL": 0.70,
            "VOLATILE": 0.40,
            "UNSTABLE": 0.20
        }
        return regime_scores.get(regime, 0.70)
    
    def calculate_pnl_consistency(self) -> float:
        """Calculate PnL consistency over last 12 hours"""
        pnl_data = self.load_json(PNL_TRACKER)
        
        # Get recent trades (last 12 hours)
        total_pnl = pnl_data.get("total_pnl", 0)
        daily_pnl = pnl_data.get("daily_pnl", 0)
        total_trades = pnl_data.get("total_trades", 0)
        
        if total_trades == 0:
            return 0.5  # Neutral score if no trades
        
        # Calculate win rate approximation
        if total_pnl > 100:
            return 0.9
        elif total_pnl > 50:
            return 0.8
        elif total_pnl > 0:
            return 0.7
        elif total_pnl > -50:
            return 0.5
        elif total_pnl > -100:
            return 0.3
        else:
            return 0.1
    
    def calculate_market_reliability_score(self) -> float:
        """
        Calculate Market Reliability Score (0-100%)
        Weighted formula:
        - AI Confidence: 40%
        - Volatility Score: 20%
        - Regime Stability: 20%
        - PnL Consistency: 20%
        """
        ai_conf = self.calculate_ai_confidence()
        volatility = self.calculate_volatility_score()
        regime = self.calculate_regime_stability()
        pnl = self.calculate_pnl_consistency()
        
        # Weighted average
        reliability = (
            (ai_conf * 0.4) +
            (volatility * 0.2) +
            (regime * 0.2) +
            (pnl * 0.2)
        ) * 100
        
        return round(min(100, max(0, reliability)), 2)
    
    def determine_risk_mode(self, reliability: float) -> Dict:
        """Determine risk mode based on reliability score"""
        if reliability >= 80:
            return RiskMode.AGGRESSIVE
        elif reliability >= 60:
            return RiskMode.BALANCED
        elif reliability >= 40:
            return RiskMode.PREVENTIVE
        elif reliability >= 20:
            return RiskMode.DEFENSIVE
        else:
            return RiskMode.SAFE_MODE
    
    def get_current_status(self) -> Dict:
        """Get current risk management status"""
        config = self.load_config()
        
        # Calculate reliability score
        reliability = self.calculate_market_reliability_score()
        
        # Determine mode
        if config.get("auto_mode", True):
            mode = self.determine_risk_mode(reliability)
        else:
            # Manual mode - use saved mode
            mode_name = config.get("current_mode", "BALANCED")
            mode = getattr(RiskMode, mode_name, RiskMode.BALANCED)
        
        # Get PnL data
        pnl_data = self.load_json(PNL_TRACKER)
        
        # Calculate drawdown
        total_pnl = pnl_data.get("total_pnl", 0)
        initial_balance = 10000  # Assuming starting balance
        current_balance = initial_balance + total_pnl
        drawdown = max(0, ((initial_balance - current_balance) / initial_balance) * 100)
        
        # Get positions count
        positions_file = self.config_dir / "positions.json"
        positions = self.load_json(positions_file)
        positions_count = len(positions) if isinstance(positions, list) else 0
        
        return {
            "reliability_score": reliability,
            "current_mode": mode["name"],
            "auto_mode": config.get("auto_mode", True),
            "max_leverage": mode["max_leverage"],
            "max_positions": mode["max_positions"],
            "current_positions": positions_count,
            "stop_loss_percent": mode["stop_loss"],
            "take_profit_percent": mode["take_profit"],
            "position_size_multiplier": mode["position_size"],
            "daily_loss_limit": config.get("daily_loss_limit", 500),
            "daily_loss_current": abs(min(0, pnl_data.get("daily_pnl", 0))),
            "max_drawdown_percent": config.get("max_drawdown_percent", 15),
            "current_drawdown_percent": round(drawdown, 2),
            "emergency_stop_active": config.get("emergency_stop_active", False),
            "mode_description": mode["description"],
            "last_update": datetime.now().isoformat()
        }
    
    def set_mode(self, mode: str, auto: bool = None) -> Dict:
        """Set risk mode manually or enable/disable auto mode"""
        config = self.load_config()
        
        if auto is not None:
            config["auto_mode"] = auto
        
        if mode and not auto:
            config["current_mode"] = mode.upper()
        
        config["last_update"] = datetime.now().isoformat()
        self.save_config(config)
        
        return self.get_current_status()
    
    def activate_emergency_stop(self) -> Dict:
        """Activate emergency stop - halt all trading"""
        config = self.load_config()
        config["emergency_stop_active"] = True
        config["auto_mode"] = False
        config["current_mode"] = "SAFE_MODE"
        config["last_update"] = datetime.now().isoformat()
        self.save_config(config)
        
        return {
            "status": "EMERGENCY_STOP_ACTIVATED",
            "message": "All trading operations halted",
            "timestamp": datetime.now().isoformat()
        }
    
    def deactivate_emergency_stop(self) -> Dict:
        """Deactivate emergency stop"""
        config = self.load_config()
        config["emergency_stop_active"] = False
        config["auto_mode"] = True
        config["current_mode"] = "BALANCED"
        config["last_update"] = datetime.now().isoformat()
        self.save_config(config)
        
        return {
            "status": "EMERGENCY_STOP_DEACTIVATED",
            "message": "Trading operations resumed",
            "timestamp": datetime.now().isoformat()
        }
    
    def add_to_history(self, event: str, details: Dict):
        """Add event to risk history"""
        config = self.load_config()
        history = config.get("risk_history", [])
        
        history.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details
        })
        
        # Keep last 100 entries
        config["risk_history"] = history[:100]
        self.save_config(config)
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get risk management history"""
        config = self.load_config()
        history = config.get("risk_history", [])
        return history[:limit]


# Global instance
risk_manager = RiskManager()
