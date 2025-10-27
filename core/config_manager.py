#!/usr/bin/env python3
"""
⚙️ SAFELOGIC SmartOrder PRO - Config Manager
============================================
Gestion centralisée de toute la configuration du bot
by MAIGA ABOUBACAR

Features:
- Chargement depuis JSON
- Validation des configs
- Hot reload (optionnel)
- Override via variables d'environnement
- Defaults sécurisés

Usage:
    from core.config_manager import get_config
    
    config = get_config()
    
    # Accès à la config
    paper_trading = config.get("trading.paper_trading")
    max_trades = config.get("trading.max_daily_trades", default=10)
    
    # Update config
    config.set("trading.mode", "auto")
    config.save()
"""

import json
import os
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
import logging

LOG = logging.getLogger("config_manager")


class ConfigManager:
    """Gestionnaire de configuration centralisé"""
    
    def __init__(self, config_path: str = "config/bot_config.json"):
        """
        Initialise le config manager
        
        Args:
            config_path: Chemin vers le fichier de config JSON
        """
        self.config_path = config_path
        self.config = {}
        self.defaults = self._get_defaults()
        
        # Charger la config
        self.load()
        
        LOG.info(f"⚙️ Config Manager initialized: {config_path}")
    
    def load(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if not Path(self.config_path).exists():
                LOG.warning(f"⚠️ Config file not found: {self.config_path}, using defaults")
                self.config = self.defaults.copy()
                # Créer le fichier avec defaults
                self.save()
                return
            
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Merge avec defaults pour les clés manquantes
            self.config = self._merge_with_defaults(self.config, self.defaults)
            
            LOG.info(f"✅ Config loaded from {self.config_path}")
        
        except Exception as e:
            LOG.error(f"❌ Error loading config: {e}")
            LOG.info("Using default configuration")
            self.config = self.defaults.copy()
    
    def save(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            # Créer le répertoire si nécessaire
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Update timestamp
            self.config["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            LOG.info(f"✅ Config saved to {self.config_path}")
            return True
        
        except Exception as e:
            LOG.error(f"❌ Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de config avec notation dot
        
        Args:
            key: Clé avec notation dot (ex: "trading.paper_trading")
            default: Valeur par défaut si clé absente
        
        Returns:
            Valeur de la config ou default
        
        Examples:
            config.get("trading.mode")  # "manual"
            config.get("trading.max_daily_trades", 10)
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            # Check environment variable override
            env_key = f"BOT_{key.replace('.', '_').upper()}"
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # Convertir le type si nécessaire
                if isinstance(value, bool):
                    return env_value.lower() in ('true', '1', 'yes')
                elif isinstance(value, int):
                    return int(env_value)
                elif isinstance(value, float):
                    return float(env_value)
                else:
                    return env_value
            
            return value
        
        except Exception as e:
            LOG.error(f"Error getting config key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any):
        """
        Définit une valeur de config avec notation dot
        
        Args:
            key: Clé avec notation dot
            value: Nouvelle valeur
        
        Examples:
            config.set("trading.mode", "auto")
            config.set("trading.paper_trading", False)
        """
        try:
            keys = key.split('.')
            config_ref = self.config
            
            # Naviguer jusqu'à l'avant-dernière clé
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            
            # Définir la valeur finale
            config_ref[keys[-1]] = value
            
            LOG.info(f"⚙️ Config updated: {key} = {value}")
        
        except Exception as e:
            LOG.error(f"Error setting config key '{key}': {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Récupère une section complète de la config
        
        Args:
            section: Nom de la section (ex: "trading", "alerts")
        
        Returns:
            Dictionnaire de la section
        """
        return self.config.get(section, {})
    
    def reload(self):
        """Recharge la configuration depuis le fichier (hot reload)"""
        LOG.info("🔄 Reloading configuration...")
        self.load()
    
    def _merge_with_defaults(self, config: Dict, defaults: Dict) -> Dict:
        """Merge config avec defaults pour les clés manquantes"""
        result = defaults.copy()
        
        for key, value in config.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_with_defaults(value, result[key])
            else:
                result[key] = value
        
        return result
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Retourne la configuration par défaut"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            
            "trading": {
                "mode": "manual",
                "paper_trading": True,
                "auto_start": False,
                "exchange": "bybit",
                "risk_level": "low",
                "max_position_size_usd": 100,
                "max_daily_trades": 10,
                "min_confidence_threshold": 0.75,
                "enable_stop_loss": True,
                "enable_take_profit": True,
                "default_leverage": 1
            },
            
            "exchanges": {
                "bybit": {
                    "enabled": True,
                    "testnet": False,
                    "api_key_env": "BYBIT_API_KEY",
                    "api_secret_env": "BYBIT_API_SECRET",
                    "recv_window": "5000",
                    "rate_limit_requests_per_minute": 50
                }
            },
            
            "strategies": {
                "auto_spot": {
                    "enabled": False,
                    "coins": ["BTC", "ETH", "SOL"],
                    "max_positions": 3,
                    "position_size_percent": 30
                },
                "auto_futures": {
                    "enabled": False,
                    "coins": ["BTCUSDT", "ETHUSDT"],
                    "leverage": 2,
                    "max_positions": 2,
                    "position_size_percent": 20
                }
            },
            
            "risk_management": {
                "max_portfolio_risk_percent": 2,
                "stop_loss_percent": 2.5,
                "take_profit_percent": 5.0,
                "trailing_stop_percent": 1.5,
                "max_drawdown_percent": 10,
                "emergency_stop_loss_percent": 5
            },
            
            "alerts": {
                "telegram": {
                    "enabled": True,
                    "bot_token_env": "TELEGRAM_BOT_TOKEN",
                    "chat_id_env": "TELEGRAM_CHAT_ID",
                    "send_on_trade": True,
                    "send_on_signal": False,
                    "send_on_error": True
                }
            },
            
            "dashboard": {
                "port": 8555,
                "host": "0.0.0.0",
                "enable_auth": True,
                "session_timeout_minutes": 60,
                "refresh_interval_seconds": 5
            },
            
            "logging": {
                "level": "INFO",
                "console_output": True,
                "file_output": True,
                "log_dir": "logs"
            }
        }
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Valide la configuration
        
        Returns:
            (is_valid, errors_list)
        """
        errors = []
        
        # Vérifier que les sections principales existent
        required_sections = ["trading", "exchanges", "strategies", "alerts", "dashboard"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Vérifier les valeurs critiques
        if self.config.get("trading", {}).get("max_position_size_usd", 0) <= 0:
            errors.append("trading.max_position_size_usd must be > 0")
        
        if self.config.get("trading", {}).get("min_confidence_threshold", 0) < 0.5:
            errors.append("trading.min_confidence_threshold should be >= 0.5")
        
        # Vérifier qu'au moins un exchange est activé
        exchanges = self.config.get("exchanges", {})
        has_active_exchange = any(
            ex.get("enabled", False) for ex in exchanges.values()
        )
        
        if not has_active_exchange:
            errors.append("At least one exchange must be enabled")
        
        return (len(errors) == 0, errors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Retourne la config complète en dict"""
        return self.config.copy()


# ========== Singleton Instance ==========

_config_instance = None


def get_config(config_path: str = "config/bot_config.json") -> ConfigManager:
    """
    Retourne l'instance singleton du config manager
    
    Args:
        config_path: Chemin vers le fichier de config
    
    Returns:
        ConfigManager instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    
    return _config_instance


if __name__ == "__main__":
    print("⚙️ Testing Config Manager...\n")
    
    config = get_config()
    
    # Test get
    print("📖 Reading config:")
    print(f"  Paper trading: {config.get('trading.paper_trading')}")
    print(f"  Max trades: {config.get('trading.max_daily_trades')}")
    print(f"  Exchange: {config.get('trading.exchange')}")
    print(f"  Dashboard port: {config.get('dashboard.port')}")
    
    # Test get section
    print("\n📂 Trading section:")
    trading = config.get_section("trading")
    print(json.dumps(trading, indent=2))
    
    # Test set
    print("\n✏️ Updating config...")
    config.set("trading.mode", "auto")
    config.set("trading.max_daily_trades", 15)
    print(f"  New mode: {config.get('trading.mode')}")
    print(f"  New max trades: {config.get('trading.max_daily_trades')}")
    
    # Test validation
    print("\n✅ Validating config...")
    is_valid, errors = config.validate()
    if is_valid:
        print("  Config is valid!")
    else:
        print("  Config has errors:")
        for error in errors:
            print(f"    - {error}")
    
    print("\n✅ Tests completed!")
