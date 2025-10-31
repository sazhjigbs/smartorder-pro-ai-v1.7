#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Watchlist Manager
=====================================
Gestionnaire de watchlist des coins à trader
by MAIGA ABOUBACAR

Features:
- Ajout/retrait manuel de coins
- Auto-scan top gainers
- Filtres (volume, market cap, blacklist)
- Synchronisation Web + Telegram
- Sauvegarde automatique config/watchlist.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import requests
from dataclasses import dataclass, asdict

# Setup logging
LOG = logging.getLogger("watchlist_manager")
LOG.setLevel(logging.INFO)

@dataclass
class CoinInfo:
    """Information sur un coin"""
    symbol: str
    exchange: str = "bybit"
    volume_24h_usd: float = 0.0
    market_cap_usd: float = 0.0
    price: float = 0.0
    change_24h: float = 0.0
    added_at: str = ""
    added_by: str = "manual"  # manual | auto_scan | api
    enabled: bool = True
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'CoinInfo':
        return CoinInfo(**data)


class WatchlistManager:
    """
    Gestionnaire de watchlist des coins à trader
    
    Fonctionnalités:
    - Ajout/retrait manuel
    - Auto-scan top gainers
    - Filtres avancés
    - Blacklist
    - Synchronisation temps réel
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize Watchlist Manager
        
        Args:
            config_dir: Répertoire de configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.watchlist_file = self.config_dir / "watchlist.json"
        self.settings_file = self.config_dir / "watchlist_settings.json"
        
        # Data structures
        self.coins: Dict[str, CoinInfo] = {}
        self.blacklist: Set[str] = set()
        self.settings = self._load_settings()
        
        # Load existing watchlist
        self._load_watchlist()
        
        LOG.info("✅ Watchlist Manager initialized")
    
    def _load_settings(self) -> Dict:
        """Charge les paramètres du watchlist"""
        default_settings = {
            "auto_scan_enabled": False,
            "scan_interval_minutes": 60,
            "min_volume_24h_usd": 100_000_000,  # 100M USD
            "min_market_cap_usd": 500_000_000,  # 500M USD
            "max_coins": 20,
            "top_gainers_count": 10,
            "min_change_24h_percent": 5.0,
            "blacklist": ["USDT", "USDC", "BUSD", "DAI", "TUSD"],
            "enabled": True
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
                LOG.info("✅ Watchlist settings loaded")
            except Exception as e:
                LOG.error(f"❌ Error loading settings: {e}")
        else:
            # Save default settings
            self._save_settings(default_settings)
        
        # Update blacklist
        self.blacklist = set(default_settings.get("blacklist", []))
        
        return default_settings
    
    def _save_settings(self, settings: Dict = None):
        """Sauvegarde les paramètres"""
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            LOG.info("✅ Settings saved")
        except Exception as e:
            LOG.error(f"❌ Error saving settings: {e}")
    
    def _load_watchlist(self):
        """Charge la watchlist depuis le fichier"""
        if self.watchlist_file.exists():
            try:
                with open(self.watchlist_file, 'r') as f:
                    data = json.load(f)
                    for symbol, coin_data in data.items():
                        self.coins[symbol] = CoinInfo.from_dict(coin_data)
                LOG.info(f"✅ Loaded {len(self.coins)} coins from watchlist")
            except Exception as e:
                LOG.error(f"❌ Error loading watchlist: {e}")
        else:
            # Create default watchlist
            self._create_default_watchlist()
    
    def _create_default_watchlist(self):
        """Crée une watchlist par défaut"""
        default_coins = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "MATIC", "DOT", "AVAX"]
        
        for coin in default_coins:
            self.add_coin(coin, added_by="default")
        
        self.save_watchlist()
        LOG.info(f"✅ Created default watchlist with {len(default_coins)} coins")
    
    def save_watchlist(self):
        """Sauvegarde la watchlist"""
        try:
            data = {symbol: coin.to_dict() for symbol, coin in self.coins.items()}
            with open(self.watchlist_file, 'w') as f:
                json.dump(data, f, indent=2)
            LOG.info(f"✅ Watchlist saved ({len(self.coins)} coins)")
            return True
        except Exception as e:
            LOG.error(f"❌ Error saving watchlist: {e}")
            return False
    
    def add_coin(self, symbol: str, exchange: str = "bybit", added_by: str = "manual") -> bool:
        """
        Ajoute un coin à la watchlist
        
        Args:
            symbol: Symbol du coin (ex: BTC, ETH)
            exchange: Exchange cible
            added_by: Source d'ajout (manual, auto_scan, api)
        
        Returns:
            True si ajout réussi
        """
        # Normalize symbol
        symbol = symbol.upper().replace("USDT", "")
        
        # Check blacklist
        if symbol in self.blacklist:
            LOG.warning(f"⚠️ Coin {symbol} is blacklisted")
            return False
        
        # Check if already exists
        if symbol in self.coins:
            LOG.info(f"ℹ️ Coin {symbol} already in watchlist")
            return False
        
        # Check max coins limit
        if len(self.coins) >= self.settings.get("max_coins", 20):
            LOG.warning(f"⚠️ Maximum coins limit reached ({len(self.coins)})")
            return False
        
        # Create coin info
        coin = CoinInfo(
            symbol=symbol,
            exchange=exchange,
            added_at=datetime.now().isoformat(),
            added_by=added_by,
            enabled=True
        )
        
        # Fetch current price and volume (optional)
        try:
            self._update_coin_data(coin)
        except Exception as e:
            LOG.warning(f"⚠️ Could not fetch data for {symbol}: {e}")
        
        self.coins[symbol] = coin
        self.save_watchlist()
        
        LOG.info(f"✅ Added {symbol} to watchlist (by {added_by})")
        return True
    
    def remove_coin(self, symbol: str) -> bool:
        """
        Retire un coin de la watchlist
        
        Args:
            symbol: Symbol du coin
        
        Returns:
            True si retrait réussi
        """
        symbol = symbol.upper().replace("USDT", "")
        
        if symbol not in self.coins:
            LOG.warning(f"⚠️ Coin {symbol} not in watchlist")
            return False
        
        del self.coins[symbol]
        self.save_watchlist()
        
        LOG.info(f"✅ Removed {symbol} from watchlist")
        return True
    
    def add_multiple_coins(self, symbols: List[str], exchange: str = "bybit", added_by: str = "manual") -> Dict:
        """
        Ajoute plusieurs coins
        
        Returns:
            Dict avec successes et failures
        """
        results = {
            "success": [],
            "failed": []
        }
        
        for symbol in symbols:
            if self.add_coin(symbol, exchange, added_by):
                results["success"].append(symbol)
            else:
                results["failed"].append(symbol)
        
        return results
    
    def remove_multiple_coins(self, symbols: List[str]) -> Dict:
        """Retire plusieurs coins"""
        results = {
            "success": [],
            "failed": []
        }
        
        for symbol in symbols:
            if self.remove_coin(symbol):
                results["success"].append(symbol)
            else:
                results["failed"].append(symbol)
        
        return results
    
    def get_coins(self, enabled_only: bool = True) -> List[CoinInfo]:
        """
        Récupère la liste des coins
        
        Args:
            enabled_only: Uniquement les coins activés
        
        Returns:
            Liste de CoinInfo
        """
        if enabled_only:
            return [coin for coin in self.coins.values() if coin.enabled]
        return list(self.coins.values())
    
    def get_coin_symbols(self, enabled_only: bool = True, with_usdt: bool = False) -> List[str]:
        """
        Récupère les symbols des coins
        
        Args:
            enabled_only: Uniquement les coins activés
            with_usdt: Ajouter USDT au symbol
        
        Returns:
            Liste de symbols
        """
        coins = self.get_coins(enabled_only)
        symbols = [coin.symbol for coin in coins]
        
        if with_usdt:
            symbols = [f"{s}USDT" for s in symbols]
        
        return symbols
    
    def enable_coin(self, symbol: str) -> bool:
        """Active un coin"""
        symbol = symbol.upper().replace("USDT", "")
        
        if symbol not in self.coins:
            return False
        
        self.coins[symbol].enabled = True
        self.save_watchlist()
        LOG.info(f"✅ Enabled {symbol}")
        return True
    
    def disable_coin(self, symbol: str) -> bool:
        """Désactive un coin"""
        symbol = symbol.upper().replace("USDT", "")
        
        if symbol not in self.coins:
            return False
        
        self.coins[symbol].enabled = False
        self.save_watchlist()
        LOG.info(f"⏸️ Disabled {symbol}")
        return True
    
    def _update_coin_data(self, coin: CoinInfo):
        """Met à jour les données d'un coin (prix, volume, etc.)"""
        # Cette fonction peut être étendue pour fetcher les données réelles depuis l'exchange
        # Pour l'instant, on met des valeurs par défaut
        pass
    
    def auto_scan_top_gainers(self, exchange: str = "bybit", count: int = None) -> Dict:
        """
        Scan automatique des top gainers
        
        Args:
            exchange: Exchange à scanner
            count: Nombre de coins à ajouter (None = use settings)
        
        Returns:
            Dict avec coins ajoutés
        """
        if count is None:
            count = self.settings.get("top_gainers_count", 10)
        
        LOG.info(f"🔍 Scanning top {count} gainers on {exchange}...")
        
        try:
            # Fetch top gainers (exemple avec CoinGecko API)
            gainers = self._fetch_top_gainers(exchange, count)
            
            results = {
                "scanned": len(gainers),
                "added": [],
                "skipped": []
            }
            
            for gainer in gainers:
                symbol = gainer["symbol"]
                
                # Apply filters
                if not self._pass_filters(gainer):
                    results["skipped"].append(symbol)
                    continue
                
                # Add to watchlist
                if self.add_coin(symbol, exchange, added_by="auto_scan"):
                    results["added"].append(symbol)
                else:
                    results["skipped"].append(symbol)
            
            LOG.info(f"✅ Auto-scan complete: {len(results['added'])} added, {len(results['skipped'])} skipped")
            return results
            
        except Exception as e:
            LOG.error(f"❌ Auto-scan failed: {e}")
            return {"scanned": 0, "added": [], "skipped": [], "error": str(e)}
    
    def _fetch_top_gainers(self, exchange: str, count: int) -> List[Dict]:
        """
        Fetch top gainers from exchange
        
        Note: Cette fonction doit être implémentée avec l'API de l'exchange
        Pour l'instant, retourne des données simulées
        """
        # TODO: Implémenter avec vraie API exchange
        # Exemple avec CoinGecko (API publique)
        
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": count * 2,  # Fetch more to have options after filtering
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Convert to internal format
            gainers = []
            for item in data:
                if item.get("price_change_percentage_24h", 0) > self.settings.get("min_change_24h_percent", 5.0):
                    gainers.append({
                        "symbol": item["symbol"].upper(),
                        "price": item["current_price"],
                        "volume_24h_usd": item.get("total_volume", 0),
                        "market_cap_usd": item.get("market_cap", 0),
                        "change_24h": item.get("price_change_percentage_24h", 0)
                    })
            
            # Sort by 24h change
            gainers.sort(key=lambda x: x["change_24h"], reverse=True)
            
            return gainers[:count]
            
        except Exception as e:
            LOG.error(f"❌ Error fetching top gainers: {e}")
            return []
    
    def _pass_filters(self, coin_data: Dict) -> bool:
        """
        Vérifie si un coin passe les filtres
        
        Args:
            coin_data: Données du coin
        
        Returns:
            True si passe tous les filtres
        """
        # Volume filter
        min_volume = self.settings.get("min_volume_24h_usd", 100_000_000)
        if coin_data.get("volume_24h_usd", 0) < min_volume:
            return False
        
        # Market cap filter
        min_mcap = self.settings.get("min_market_cap_usd", 500_000_000)
        if coin_data.get("market_cap_usd", 0) < min_mcap:
            return False
        
        # Blacklist filter
        if coin_data["symbol"] in self.blacklist:
            return False
        
        return True
    
    def add_to_blacklist(self, symbol: str):
        """Ajoute un coin à la blacklist"""
        symbol = symbol.upper().replace("USDT", "")
        self.blacklist.add(symbol)
        
        # Remove from watchlist if present
        if symbol in self.coins:
            self.remove_coin(symbol)
        
        # Update settings
        self.settings["blacklist"] = list(self.blacklist)
        self._save_settings()
        
        LOG.info(f"✅ Added {symbol} to blacklist")
    
    def remove_from_blacklist(self, symbol: str):
        """Retire un coin de la blacklist"""
        symbol = symbol.upper().replace("USDT", "")
        if symbol in self.blacklist:
            self.blacklist.remove(symbol)
            
            # Update settings
            self.settings["blacklist"] = list(self.blacklist)
            self._save_settings()
            
            LOG.info(f"✅ Removed {symbol} from blacklist")
    
    def update_settings(self, new_settings: Dict):
        """Met à jour les paramètres"""
        self.settings.update(new_settings)
        
        # Update blacklist if changed
        if "blacklist" in new_settings:
            self.blacklist = set(new_settings["blacklist"])
        
        self._save_settings()
        LOG.info("✅ Settings updated")
    
    def get_stats(self) -> Dict:
        """Statistiques de la watchlist"""
        enabled_coins = [c for c in self.coins.values() if c.enabled]
        
        return {
            "total_coins": len(self.coins),
            "enabled_coins": len(enabled_coins),
            "disabled_coins": len(self.coins) - len(enabled_coins),
            "blacklist_size": len(self.blacklist),
            "manual_added": len([c for c in self.coins.values() if c.added_by == "manual"]),
            "auto_scan_added": len([c for c in self.coins.values() if c.added_by == "auto_scan"]),
            "max_coins": self.settings.get("max_coins", 20),
            "auto_scan_enabled": self.settings.get("auto_scan_enabled", False)
        }


# Singleton instance
_watchlist_manager = None

def get_watchlist_manager() -> WatchlistManager:
    """Get singleton instance of WatchlistManager"""
    global _watchlist_manager
    if _watchlist_manager is None:
        _watchlist_manager = WatchlistManager()
    return _watchlist_manager


if __name__ == "__main__":
    # Test du Watchlist Manager
    print("🔥 Testing Watchlist Manager...")
    
    wm = WatchlistManager()
    
    # Test add coins
    print("\n➕ Adding coins...")
    wm.add_coin("BTC")
    wm.add_coin("ETH")
    wm.add_coin("SOL")
    
    # Test get coins
    print(f"\n📋 Coins: {wm.get_coin_symbols()}")
    
    # Test stats
    print(f"\n📊 Stats: {json.dumps(wm.get_stats(), indent=2)}")
    
    # Test auto-scan (if enabled)
    # wm.auto_scan_top_gainers(count=5)
    
    print("\n✅ Watchlist Manager test complete!")
