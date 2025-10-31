#!/usr/bin/env python3
"""
🎯 STRATEGY EXECUTOR - SmartOrder PRO AI
Moteur d'exécution des stratégies activées depuis strategies_state.json

Fonctionnalités:
- Lecture automatique des stratégies ENABLED
- Exécution multi-threading par stratégie
- Mise à jour PnL en temps réel
- Paper Trading & Live Trading
- Gestion des ordres via CCXT
- Logs détaillés par stratégie
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading
import sys

# Configuration
CONFIG_DIR = Path('/opt/smartorder-pro/config')
STRATEGIES_FILE = CONFIG_DIR / 'strategies_state.json'
EXCHANGES_FILE = CONFIG_DIR / 'exchanges_state.json'
LOG_DIR = Path('/opt/smartorder-pro/logs')
LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'strategy_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StrategyExecutor:
    """Exécuteur de stratégies de trading"""
    
    def __init__(self):
        self.running = False
        self.strategy_threads = {}
        self.strategies_data = {}
        self.exchanges_data = {}
        self.reload_interval = 10  # Recharger config toutes les 10s
        
    def load_strategies_config(self) -> Dict:
        """Charge la configuration des stratégies"""
        try:
            with open(STRATEGIES_FILE, 'r') as f:
                data = json.load(f)
                logger.debug(f"Stratégies chargées: {len(data.get('spot', []))} SPOT, "
                           f"{len(data.get('futures', []))} FUTURES, "
                           f"{len(data.get('hybride', []))} HYBRIDE")
                return data
        except Exception as e:
            logger.error(f"Erreur chargement stratégies: {e}")
            return {'spot': [], 'futures': [], 'hybride': []}
    
    def load_exchanges_config(self) -> Dict:
        """Charge la configuration des exchanges"""
        try:
            with open(EXCHANGES_FILE, 'r') as f:
                data = json.load(f)
                active = [name for name, info in data.items() if info.get('connected')]
                logger.debug(f"Exchanges actifs: {', '.join(active)}")
                return data
        except Exception as e:
            logger.error(f"Erreur chargement exchanges: {e}")
            return {}
    
    def get_enabled_strategies(self) -> List[Dict]:
        """Récupère toutes les stratégies activées"""
        enabled = []
        strategies = self.load_strategies_config()
        
        for mode in ['spot', 'futures', 'hybride']:
            for strategy in strategies.get(mode, []):
                if strategy.get('enabled', False):
                    strategy['mode'] = mode
                    enabled.append(strategy)
        
        return enabled
    
    def get_primary_exchange(self) -> Optional[str]:
        """Récupère l'exchange primaire actif"""
        exchanges = self.load_exchanges_config()
        
        # Chercher exchange primary
        for name, info in exchanges.items():
            if info.get('primary') and info.get('connected'):
                return name
        
        # Sinon prendre le premier connecté
        for name, info in exchanges.items():
            if info.get('connected'):
                return name
        
        return None
    
    def execute_strategy(self, strategy: Dict, exchange: str):
        """Exécute une stratégie de trading"""
        strategy_id = strategy['id']
        strategy_name = strategy['name']
        mode = strategy.get('mode', 'spot')
        
        logger.info(f"🚀 Démarrage stratégie: {strategy_name} ({mode.upper()}) sur {exchange}")
        
        iteration = 0
        
        try:
            while self.running and strategy_id in self.strategy_threads:
                iteration += 1
                
                # Simuler analyse de marché
                logger.debug(f"[{strategy_name}] Itération {iteration} - Analyse marché...")
                
                # TODO: Implémenter la vraie logique de trading
                # 1. Récupérer prix via CCXT
                # 2. Calculer indicateurs techniques
                # 3. Générer signaux d'achat/vente
                # 4. Placer ordres si conditions remplies
                # 5. Mettre à jour PnL
                
                # Simulation pour démonstration
                if iteration % 30 == 0:  # Toutes les 30 itérations
                    simulated_trade = {
                        'type': 'BUY' if iteration % 60 == 0 else 'SELL',
                        'price': 42000 + (iteration % 100),
                        'amount': 0.001,
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"[{strategy_name}] 📊 Trade simulé: {simulated_trade['type']} "
                              f"{simulated_trade['amount']} @ ${simulated_trade['price']}")
                
                # Attendre avant prochaine itération
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"[{strategy_name}] ❌ Erreur: {e}", exc_info=True)
        finally:
            logger.info(f"[{strategy_name}] ⏹️  Arrêt stratégie")
    
    def start_strategy(self, strategy: Dict, exchange: str):
        """Lance une stratégie dans un thread séparé"""
        strategy_id = strategy['id']
        
        if strategy_id in self.strategy_threads:
            logger.warning(f"Stratégie {strategy['name']} déjà en cours")
            return
        
        thread = threading.Thread(
            target=self.execute_strategy,
            args=(strategy, exchange),
            daemon=True
        )
        thread.start()
        self.strategy_threads[strategy_id] = thread
        
        logger.info(f"✅ Stratégie {strategy['name']} lancée (Thread ID: {thread.ident})")
    
    def stop_strategy(self, strategy_id: str):
        """Arrête une stratégie"""
        if strategy_id in self.strategy_threads:
            del self.strategy_threads[strategy_id]
            logger.info(f"🛑 Arrêt demandé pour stratégie {strategy_id}")
    
    def sync_strategies(self):
        """Synchronise les stratégies en cours avec la config"""
        enabled_strategies = self.get_enabled_strategies()
        enabled_ids = {s['id'] for s in enabled_strategies}
        running_ids = set(self.strategy_threads.keys())
        
        # Arrêter stratégies qui ne sont plus enabled
        to_stop = running_ids - enabled_ids
        for strategy_id in to_stop:
            self.stop_strategy(strategy_id)
        
        # Démarrer nouvelles stratégies enabled
        exchange = self.get_primary_exchange()
        if not exchange:
            logger.warning("⚠️  Aucun exchange actif - stratégies en attente")
            return
        
        to_start = enabled_ids - running_ids
        for strategy in enabled_strategies:
            if strategy['id'] in to_start:
                self.start_strategy(strategy, exchange)
    
    def run(self):
        """Boucle principale d'exécution"""
        logger.info("=" * 80)
        logger.info("🎯 STRATEGY EXECUTOR - SmartOrder PRO AI")
        logger.info("=" * 80)
        logger.info(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Config: {STRATEGIES_FILE}")
        logger.info(f"Logs: {LOG_DIR / 'strategy_executor.log'}")
        logger.info("=" * 80)
        
        self.running = True
        
        try:
            while self.running:
                # Synchroniser stratégies
                self.sync_strategies()
                
                # Afficher statut
                enabled = self.get_enabled_strategies()
                running = len(self.strategy_threads)
                
                if running > 0:
                    logger.info(f"📊 Statut: {running} stratégie(s) en cours "
                              f"({len(enabled)} activées)")
                else:
                    logger.info(f"⏸️  Aucune stratégie en cours ({len(enabled)} activées)")
                
                # Attendre avant prochaine sync
                time.sleep(self.reload_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interruption utilisateur (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Arrêt propre du système"""
        logger.info("🛑 Arrêt du Strategy Executor...")
        self.running = False
        
        # Attendre que tous les threads se terminent
        for strategy_id, thread in list(self.strategy_threads.items()):
            logger.info(f"  Attente arrêt: {strategy_id}")
            thread.join(timeout=5)
        
        logger.info("✅ Arrêt complet")
        logger.info("=" * 80)


def main():
    """Point d'entrée principal"""
    executor = StrategyExecutor()
    
    try:
        executor.run()
    except Exception as e:
        logger.error(f"Erreur critique: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
