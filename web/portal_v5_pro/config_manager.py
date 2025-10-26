#!/usr/bin/env python3
"""
⚙️ SAFELOGIC SmartOrder PRO — Live Configuration Manager
Manage runtime settings without restart
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class ConfigManager:
    """
    Manages live configuration that can be updated without restarting
    """
    
    def __init__(self, config_file: str = "live_config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.default_config = self._get_default_config()
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration values"""
        return {
            "trading": {
                "enabled": True,
                "mode": "auto",  # auto, manual, paper
                "max_positions": 5,
                "max_position_size": 1000,
                "risk_per_trade": 2.0,  # percentage
                "leverage": 1,
                "stop_loss_percent": 2.0,
                "take_profit_percent": 4.0,
                "trailing_stop": False,
                "trailing_stop_percent": 1.5
            },
            "risk_management": {
                "max_daily_loss": 500,
                "max_daily_trades": 20,
                "max_drawdown_percent": 10,
                "circuit_breaker_enabled": True,
                "cooldown_after_loss": 300,  # seconds
                "min_risk_reward_ratio": 1.5
            },
            "exchanges": {
                "bybit": {
                    "enabled": True,
                    "testnet": True,
                    "api_key": os.getenv("BYBIT_API_KEY", ""),
                    "api_secret": os.getenv("BYBIT_API_SECRET", "")
                },
                "binance": {
                    "enabled": False,
                    "testnet": True,
                    "api_key": os.getenv("BINANCE_API_KEY", ""),
                    "api_secret": os.getenv("BINANCE_API_SECRET", "")
                }
            },
            "strategies": {
                "active_strategy": "hybrid",
                "strategies": {
                    "scalping": {
                        "enabled": False,
                        "timeframe": "1m",
                        "indicators": ["rsi", "macd"]
                    },
                    "swing": {
                        "enabled": False,
                        "timeframe": "4h",
                        "indicators": ["ema", "bollinger"]
                    },
                    "hybrid": {
                        "enabled": True,
                        "timeframe": "5m",
                        "indicators": ["all"]
                    }
                }
            },
            "notifications": {
                "telegram": {
                    "enabled": True,
                    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
                    "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
                    "notify_on_trade": True,
                    "notify_on_profit": True,
                    "notify_on_loss": True
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": os.getenv("SMTP_USER", ""),
                    "password": os.getenv("SMTP_PASSWORD", ""),
                    "to_email": os.getenv("USER_EMAIL", "")
                }
            },
            "advanced": {
                "log_level": "INFO",
                "save_trade_history": True,
                "backup_interval_hours": 24,
                "api_rate_limit": 50,
                "websocket_reconnect": True,
                "data_retention_days": 90
            },
            "ui": {
                "theme": "dark",
                "language": "en",
                "refresh_interval": 5,  # seconds
                "show_advanced_metrics": True,
                "compact_mode": False
            }
        }
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print(f"✅ Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Create backup
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                with open(self.config_file, 'r') as f:
                    with open(backup_file, 'w') as bf:
                        bf.write(f.read())
            
            # Save new config
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            print(f"✅ Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation path
        Example: config.get('trading.max_positions')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set config value by dot-notation path
        Example: config.set('trading.max_positions', 10)
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        return self.save_config()
    
    def get_section(self, section: str) -> Dict:
        """Get entire configuration section"""
        return self.config.get(section, {})
    
    def update_section(self, section: str, values: Dict) -> bool:
        """Update entire configuration section"""
        if section in self.config:
            self.config[section].update(values)
            return self.save_config()
        return False
    
    def reset_to_default(self, section: Optional[str] = None) -> bool:
        """Reset configuration to default values"""
        if section:
            if section in self.default_config:
                self.config[section] = self.default_config[section].copy()
        else:
            self.config = self.default_config.copy()
        
        return self.save_config()
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration and return errors"""
        errors = {}
        
        # Validate trading config
        trading = self.config.get('trading', {})
        if trading.get('max_positions', 0) <= 0:
            errors.setdefault('trading', []).append('max_positions must be positive')
        
        if trading.get('risk_per_trade', 0) <= 0 or trading.get('risk_per_trade', 0) > 100:
            errors.setdefault('trading', []).append('risk_per_trade must be between 0 and 100')
        
        # Validate risk management
        risk = self.config.get('risk_management', {})
        if risk.get('max_daily_loss', 0) <= 0:
            errors.setdefault('risk_management', []).append('max_daily_loss must be positive')
        
        # Validate exchanges
        exchanges = self.config.get('exchanges', {})
        for exchange, config in exchanges.items():
            if config.get('enabled') and not config.get('api_key'):
                errors.setdefault('exchanges', []).append(f'{exchange} enabled but no API key')
        
        return errors
    
    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self.config, indent=2)
    
    def import_config(self, config_json: str) -> bool:
        """Import configuration from JSON string"""
        try:
            new_config = json.loads(config_json)
            self.config = new_config
            return self.save_config()
        except Exception as e:
            print(f"❌ Error importing config: {e}")
            return False
    
    def get_changelog(self) -> list:
        """Get configuration change history (if available)"""
        changelog_file = f"{self.config_file}.changelog"
        
        if os.path.exists(changelog_file):
            try:
                with open(changelog_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def log_change(self, user: str, section: str, key: str, old_value: Any, new_value: Any):
        """Log configuration change"""
        changelog_file = f"{self.config_file}.changelog"
        
        change = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "section": section,
            "key": key,
            "old_value": old_value,
            "new_value": new_value
        }
        
        changelog = self.get_changelog()
        changelog.append(change)
        
        # Keep only last 100 changes
        changelog = changelog[-100:]
        
        try:
            with open(changelog_file, 'w') as f:
                json.dump(changelog, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error logging change: {e}")

# Global config instance
config_manager = ConfigManager()
