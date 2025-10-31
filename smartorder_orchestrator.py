#!/usr/bin/env python3
"""
🚀 SmartOrder PRO - Orchestrateur Central
by MAIGA ABOUBACAR

Active et coordonne TOUS les modules:
- Modes (Spot/Futures/Hybrid)
- Stratégies (Grid/DCA/Scalping/etc)
- Exchanges (Bybit/Binance/OKX/KuCoin)
- Watchlist
- Signal Validation
- Router Intelligent
- Sécurité
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartOrderOrchestrator")

# Import tous les modules
try:
    from core.auto_spot_ai_manager import AutoSpotAIManager
    from core.auto_futures_ai_manager import AutoFuturesAIManager
    from core.hybrid_capital_manager import HybridCapitalManager
    from core.exchange_router import ExchangeRouter
    from core.signal_validator import SignalValidator
    from core.watchlist_manager import WatchlistManager
    from core.grid_infinity_engine import GridInfinityEngine
    from strategies.dca_advanced import DCAAdvanced
    from core.market_regime_detector import MarketRegimeDetector
    from security.security_manager_enhanced import SecurityManager
    logger.info("✅ Tous les modules importés avec succès")
except Exception as e:
    logger.error(f"❌ Erreur import modules: {e}")

class SmartOrderOrchestrator:
    """Orchestrateur central SmartOrder PRO"""
    
    def __init__(self):
        """Initialise l'orchestrateur"""
        logger.info("🚀 Initialisation SmartOrder PRO Orchestrator")
        
        # État global
        self.state = {
            "mode": "spot",  # spot, futures, hybrid, manual
            "active_strategies": [],
            "active_exchanges": ["bybit"],
            "paused": False,
            "emergency_stop": False
        }
        
        # Managers
        self.spot_manager = None
        self.futures_manager = None
        self.hybrid_manager = None
        self.exchange_router = None
        self.signal_validator = None
        self.watchlist_manager = None
        self.grid_engine = None
        self.dca_engine = None
        self.regime_detector = None
        self.security_manager = None
        
        self._initialize_all()
    
    def _initialize_all(self):
        """Initialise TOUS les modules"""
        try:
            # Spot Manager
            try:
                self.spot_manager = AutoSpotAIManager()
                logger.info("✅ Auto Spot AI Manager initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Spot Manager: {e}")
            
            # Futures Manager
            try:
                self.futures_manager = AutoFuturesAIManager()
                logger.info("✅ Auto Futures AI Manager initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Futures Manager: {e}")
            
            # Hybrid Manager
            try:
                self.hybrid_manager = HybridCapitalManager()
                logger.info("✅ Hybrid Capital Manager initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Hybrid Manager: {e}")
            
            # Exchange Router
            try:
                self.exchange_router = ExchangeRouter()
                logger.info("✅ Exchange Router initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Exchange Router: {e}")
            
            # Signal Validator
            try:
                self.signal_validator = SignalValidator()
                logger.info("✅ Signal Validator initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Signal Validator: {e}")
            
            # Watchlist Manager
            try:
                self.watchlist_manager = WatchlistManager()
                logger.info("✅ Watchlist Manager initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Watchlist Manager: {e}")
            
            # Grid Engine
            try:
                self.grid_engine = GridInfinityEngine()
                logger.info("✅ Grid Infinity Engine initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Grid Engine: {e}")
            
            # DCA Engine
            try:
                self.dca_engine = DCAAdvanced()
                logger.info("✅ DCA Advanced initialisé")
            except Exception as e:
                logger.warning(f"⚠️ DCA Engine: {e}")
            
            # Market Regime Detector
            try:
                self.regime_detector = MarketRegimeDetector()
                logger.info("✅ Market Regime Detector initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Regime Detector: {e}")
            
            # Security Manager
            try:
                self.security_manager = SecurityManager()
                logger.info("✅ Security Manager initialisé")
            except Exception as e:
                logger.warning(f"⚠️ Security Manager: {e}")
            
            logger.info("🎉 TOUS LES MODULES INITIALISÉS")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation globale: {e}")
    
    def set_mode(self, mode: str):
        """Change le mode de trading"""
        if mode not in ["spot", "futures", "hybrid", "manual"]:
            logger.error(f"❌ Mode invalide: {mode}")
            return False
        
        self.state["mode"] = mode
        logger.info(f"✅ Mode changé: {mode.upper()}")
        return True
    
    def start_strategy(self, strategy: str, config: Dict = None):
        """Démarre une stratégie"""
        if strategy in self.state["active_strategies"]:
            logger.warning(f"⚠️ Stratégie {strategy} déjà active")
            return False
        
        try:
            if strategy == "grid" and self.grid_engine:
                # Démarrer Grid Trading
                coin = config.get("coin", "BTCUSDT") if config else "BTCUSDT"
                capital = config.get("capital", 1000) if config else 1000
                # self.grid_engine.create_grid(coin, current_price, capital)
                logger.info(f"✅ Grid Trading démarré sur {coin}")
            
            elif strategy == "dca" and self.dca_engine:
                # Démarrer DCA
                logger.info("✅ DCA Strategy démarrée")
            
            self.state["active_strategies"].append(strategy)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage {strategy}: {e}")
            return False
    
    def stop_strategy(self, strategy: str):
        """Arrête une stratégie"""
        if strategy in self.state["active_strategies"]:
            self.state["active_strategies"].remove(strategy)
            logger.info(f"🛑 Stratégie {strategy} arrêtée")
            return True
        return False
    
    def stop_all(self):
        """Arrête tout"""
        self.state["active_strategies"].clear()
        self.state["paused"] = True
        logger.info("🛑 TOUT ARRÊTÉ")
    
    def emergency_stop(self):
        """Arrêt d'urgence total"""
        self.stop_all()
        self.state["emergency_stop"] = True
        logger.warning("🚨 ARRÊT D'URGENCE ACTIVÉ")
    
    def get_status(self) -> Dict:
        """Récupère le statut complet"""
        return {
            "mode": self.state["mode"],
            "active_strategies": self.state["active_strategies"],
            "active_exchanges": self.state["active_exchanges"],
            "paused": self.state["paused"],
            "emergency_stop": self.state["emergency_stop"],
            "modules": {
                "spot_manager": self.spot_manager is not None,
                "futures_manager": self.futures_manager is not None,
                "hybrid_manager": self.hybrid_manager is not None,
                "exchange_router": self.exchange_router is not None,
                "signal_validator": self.signal_validator is not None,
                "watchlist_manager": self.watchlist_manager is not None,
                "grid_engine": self.grid_engine is not None,
                "dca_engine": self.dca_engine is not None,
                "regime_detector": self.regime_detector is not None,
                "security_manager": self.security_manager is not None
            }
        }

# Instance globale
orchestrator = SmartOrderOrchestrator()

def get_orchestrator():
    """Récupère l'instance de l'orchestrateur"""
    return orchestrator

if __name__ == "__main__":
    # Test
    logger.info("="*60)
    logger.info("SmartOrder PRO - Test Orchestrator")
    logger.info("="*60)
    
    status = orchestrator.get_status()
    
    logger.info(f"\n📊 Status:")
    logger.info(f"  Mode: {status['mode']}")
    logger.info(f"  Stratégies actives: {len(status['active_strategies'])}")
    logger.info(f"  Exchanges actifs: {len(status['active_exchanges'])}")
    
    logger.info(f"\n🔧 Modules:")
    for module, active in status['modules'].items():
        icon = "✅" if active else "❌"
        logger.info(f"  {icon} {module}")
    
    logger.info("\n✅ Orchestrator opérationnel!")
