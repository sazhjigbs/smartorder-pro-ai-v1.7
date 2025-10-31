"""
SmartOrder PRO AI - Strategy Executor v2.1
===========================================
Exécuteur de stratégies pilotable dynamiquement par Dashboard.

Fonctionnalités P4:
- Chargement trading_modes.json via adaptateurs
- Respect strict du mode actif (spot/futures/hybrid/manual)
- Exécution uniquement des stratégies enabled:true
- Rechargement config à chaud sans redémarrage
- Logs traçables décision → exécution
- Support AI Selector pour sélection automatique

Version: v2.1-P4-FINAL
Date: 2025-10-31
"""

import sys
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path

# Setup paths
sys.path.insert(0, "/opt/smartorder-pro")

# Import adapters
from adapters.config_adapter import (
    read_trading_modes,
    read_risk_config,
    read_watchlist,
    read_wallet,
    write_wallet
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/opt/smartorder-pro/logs/strategy_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Exécuteur principal de stratégies trading.
    Pilotable en temps réel via Dashboard P4.
    """
    
    def __init__(self):
        """Initialisation et chargement configuration."""
        logger.info("="*80)
        logger.info("[INIT] SmartOrder PRO AI - Strategy Executor v2.1")
        logger.info("="*80)
        
        # Chargement configurations
        self.trading_config = self.load_trading_config()
        self.risk_config = read_risk_config()
        self.watchlist = read_watchlist()
        self.wallet = read_wallet()
        
        # État actuel
        self.current_mode = self.trading_config.get("current_mode", "spot")
        self.ai_selector_enabled = self.trading_config.get("ai_selector", {}).get("enabled", False)
        self.enabled_strategies = self.get_enabled_strategies()
        
        # Logs initialisation
        logger.info(f"[INIT] Mode actif: {self.current_mode.upper()}")
        logger.info(f"[INIT] AI Selector: {'ENABLED' if self.ai_selector_enabled else 'DISABLED'}")
        logger.info(f"[INIT] Stratégies enabled: {[s['label'] for s in self.enabled_strategies]}")
        logger.info(f"[INIT] Watchlist: {len(self.watchlist)} paires")
        logger.info(f"[INIT] Wallet USDT: {self.wallet.get('USDT', 0):.2f}")
        logger.info("="*80)
    
    def load_trading_config(self):
        """Charge trading_modes.json via adaptateur."""
        try:
            config = read_trading_modes()
            logger.info("[CONFIG] trading_modes.json chargé avec succès")
            return config
        except Exception as e:
            logger.error(f"[CONFIG ERROR] Impossible de charger trading_modes.json: {e}")
            # Config par défaut minimale
            return {
                "current_mode": "spot",
                "strategies": {"spot": [], "futures": [], "hybrid": []},
                "ai_selector": {"enabled": False}
            }
    
    def get_enabled_strategies(self):
        """Retourne uniquement les stratégies enabled du mode actif."""
        mode_strategies = self.trading_config.get("strategies", {}).get(self.current_mode, [])
        enabled = [s for s in mode_strategies if s.get("enabled", False)]
        
        logger.info(f"[FILTER] Mode '{self.current_mode}': {len(mode_strategies)} stratégies disponibles, {len(enabled)} enabled")
        
        return enabled
    
    def reload_config(self):
        """
        Recharge la configuration à chaud (changements Dashboard).
        Appelé à chaque cycle pour détecter modifications UI.
        """
        try:
            self.trading_config = self.load_trading_config()
            new_mode = self.trading_config.get("current_mode")
            new_ai_enabled = self.trading_config.get("ai_selector", {}).get("enabled", False)
            
            # Détection changement mode
            if new_mode != self.current_mode:
                logger.warning(f"[CONFIG RELOAD] ⚠️  Changement de mode détecté: {self.current_mode} → {new_mode}")
                self.current_mode = new_mode
            
            # Détection changement AI Selector
            if new_ai_enabled != self.ai_selector_enabled:
                logger.warning(f"[CONFIG RELOAD] ⚠️  AI Selector: {self.ai_selector_enabled} → {new_ai_enabled}")
                self.ai_selector_enabled = new_ai_enabled
            
            # Recharger stratégies enabled
            old_count = len(self.enabled_strategies)
            self.enabled_strategies = self.get_enabled_strategies()
            new_count = len(self.enabled_strategies)
            
            if old_count != new_count:
                logger.warning(f"[CONFIG RELOAD] ⚠️  Stratégies enabled: {old_count} → {new_count}")
            
            # Recharger autres configs
            self.risk_config = read_risk_config()
            self.watchlist = read_watchlist()
            
        except Exception as e:
            logger.error(f"[CONFIG RELOAD ERROR] {e}")
    
    def execute_trading_cycle(self):
        """
        Exécute un cycle de trading complet.
        Respecte strictement mode actif et stratégies enabled.
        """
        logger.info("")
        logger.info("="*80)
        logger.info(f"[CYCLE START] Mode: {self.current_mode.upper()} | AI Selector: {self.ai_selector_enabled}")
        logger.info("="*80)
        
        # Vérifier stratégies actives
        if len(self.enabled_strategies) == 0:
            logger.warning("[CYCLE] ⚠️  Aucune stratégie active - cycle ignoré")
            return
        
        logger.info(f"[CYCLE] {len(self.enabled_strategies)} stratégies actives à exécuter")
        
        # Si AI Selector activé, sélectionner meilleure stratégie
        if self.ai_selector_enabled:
            selected_strategy = self.ai_select_best_strategy()
            if selected_strategy:
                strategies_to_execute = [selected_strategy]
                logger.info(f"[AI SELECTOR] ✅ Stratégie sélectionnée: {selected_strategy['label']} (Score: {selected_strategy.get('last_score', 0)})")
            else:
                logger.warning("[AI SELECTOR] ⚠️  Aucune stratégie éligible (score < min_score_to_trade)")
                return
        else:
            # Mode normal: exécuter toutes les stratégies enabled
            strategies_to_execute = self.enabled_strategies
        
        # Exécuter stratégies
        for strategy in strategies_to_execute:
            self.execute_strategy(strategy)
        
        logger.info("="*80)
        logger.info(f"[CYCLE END] Cycle terminé - {len(strategies_to_execute)} stratégies exécutées")
        logger.info("="*80)
    
    def execute_strategy(self, strategy):
        """
        Exécute une stratégie spécifique sur toutes les paires watchlist.
        """
        strategy_id = strategy["id"]
        strategy_label = strategy["label"]
        
        logger.info(f"[EXECUTE] >>> Stratégie: {strategy_label} (ID: {strategy_id})")
        
        try:
            # Vérifier paramètres stratégie
            params = strategy.get("params", {})
            indicators = strategy.get("indicators", [])
            
            logger.info(f"[EXECUTE]     Indicateurs: {', '.join(indicators)}")
            logger.info(f"[EXECUTE]     Timeframe: {params.get('timeframe', 'N/A')}")
            logger.info(f"[EXECUTE]     TP/SL: {params.get('tp_pct', 0)}% / {params.get('sl_pct', 0)}%")
            
            # Exécuter sur chaque paire de la watchlist
            for pair in self.watchlist:
                symbol = pair.get("symbol")
                exchange = pair.get("exchange")
                
                if not pair.get("active", False):
                    continue
                
                # Simuler analyse + décision trading
                decision = self.analyze_and_decide(strategy, symbol, exchange)
                
                if decision["action"] != "HOLD":
                    self.log_decision(strategy_id, symbol, decision)
                    # self.execute_trade(decision)  # Exécution réelle désactivée (paper trading)
            
            logger.info(f"[SUCCESS] ✅ {strategy_label} exécutée avec succès")
        
        except Exception as e:
            logger.error(f"[ERROR] ❌ {strategy_label} erreur: {e}")
    
    def analyze_and_decide(self, strategy, symbol, exchange):
        """
        Analyse marché et prend décision trading pour une stratégie/paire.
        Simplifié pour démo - à remplacer par analyse réelle.
        """
        strategy_id = strategy["id"]
        
        # Simulation décision (remplacer par analyse réelle RSI, MACD, etc.)
        import random
        actions = ["BUY", "SELL", "HOLD"]
        weights = [0.15, 0.15, 0.70]  # 15% BUY, 15% SELL, 70% HOLD
        
        action = random.choices(actions, weights=weights)[0]
        
        if action == "HOLD":
            return {"action": "HOLD"}
        
        # Raisons fictives (remplacer par analyse réelle)
        reasons = {
            "BUY": ["RSI < 30 (oversold)", "MACD crossover bullish", "Price below SMA20"],
            "SELL": ["RSI > 70 (overbought)", "MACD crossover bearish", "Price above BB upper band"]
        }
        
        reason = random.choice(reasons.get(action, ["Market condition"]))
        
        return {
            "action": action,
            "symbol": symbol,
            "exchange": exchange,
            "strategy_id": strategy_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def log_decision(self, strategy_id, symbol, decision):
        """Log décision trading pour traçabilité."""
        log_entry = {
            "timestamp": decision["timestamp"],
            "mode": self.current_mode,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "action": decision["action"],
            "reason": decision["reason"]
        }
        
        # Log console
        logger.info(f"[DECISION] {strategy_id} | {symbol} | {decision['action']} | {decision['reason']}")
        
        # Log fichier JSONL
        try:
            log_file = Path("/opt/smartorder-pro/logs/strategy_decisions.jsonl")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"[LOG ERROR] Impossible d'écrire strategy_decisions.jsonl: {e}")
    
    def ai_select_best_strategy(self):
        """
        Sélectionne automatiquement la meilleure stratégie via AI Selector.
        Basé sur scores calculés + seuil min_score_to_trade.
        """
        ai_config = self.trading_config.get("ai_selector", {})
        min_score = ai_config.get("min_score_to_trade", 70)
        
        # Filtrer stratégies éligibles (ai_allowed + score suffisant)
        eligible = [
            s for s in self.enabled_strategies 
            if s.get("ai_allowed", False) and s.get("last_score", 0) >= min_score
        ]
        
        if not eligible:
            return None
        
        # Trier par score décroissant
        eligible_sorted = sorted(eligible, key=lambda s: s.get("last_score", 0), reverse=True)
        
        # Log top 3
        logger.info(f"[AI SELECTOR] {len(eligible)} stratégies éligibles (score >= {min_score})")
        for i, s in enumerate(eligible_sorted[:3], 1):
            logger.info(f"[AI SELECTOR]     #{i}: {s['label']} - Score: {s.get('last_score', 0)}")
        
        # Retourner la meilleure
        return eligible_sorted[0]
    
    def run(self, interval_seconds=60):
        """
        Boucle principale d'exécution.
        Recharge config à chaque cycle pour détecter changements Dashboard.
        """
        logger.info("[RUN] Démarrage de la boucle principale")
        logger.info(f"[RUN] Intervalle entre cycles: {interval_seconds}s")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n[ITERATION {iteration}] Début")
                
                # Recharger config (détecte changements Dashboard)
                self.reload_config()
                
                # Exécuter cycle trading
                self.execute_trading_cycle()
                
                logger.info(f"[ITERATION {iteration}] Fin - Attente {interval_seconds}s")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n[RUN] Arrêt demandé par utilisateur (Ctrl+C)")
        except Exception as e:
            logger.error(f"[RUN ERROR] Erreur fatale: {e}")
            raise


def main():
    """Point d'entrée principal."""
    try:
        executor = StrategyExecutor()
        executor.run(interval_seconds=60)  # Cycle toutes les 60 secondes
    except Exception as e:
        logger.error(f"[MAIN ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
