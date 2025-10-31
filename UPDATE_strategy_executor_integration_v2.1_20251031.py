#!/usr/bin/env python3
"""
UPDATE: Strategy Executor Integration v2.1
Date: 2025-10-31
Description: Integration des nouveaux modules dans strategy_executor.py
             SANS ecraser l'existant - methode progressive
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

# Paths
SMARTORDER_PATH = Path("/opt/smartorder-pro")
STRATEGY_EXECUTOR = SMARTORDER_PATH / "strategy_executor.py"
BACKUP_PATH = SMARTORDER_PATH / "backups"
UPDATES_PATH = SMARTORDER_PATH / "updates"

def create_backup():
    """Backup du strategy_executor.py actuel"""
    BACKUP_PATH.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_PATH / f"strategy_executor_v2.0_{timestamp}.py"
    shutil.copy(STRATEGY_EXECUTOR, backup_file)
    print(f"✅ Backup cree: {backup_file}")
    return backup_file

def read_current_executor():
    """Lit le contenu actuel"""
    with open(STRATEGY_EXECUTOR, 'r') as f:
        return f.read()

def create_integrated_executor():
    """Cree la version integree avec les nouveaux modules"""
    
    integrated_code = '''#!/usr/bin/env python3
"""
🎯 STRATEGY EXECUTOR v2.1 - SmartOrder PRO AI
Moteur d'execution des strategies avec Risk Management + Technical Indicators + CCXT

Changelog v2.1:
- Risk Management integre (stop-loss, take-profit, drawdown guard)
- Technical Indicators (RSI, MACD, Bollinger Bands)
- CCXT Integration (connexions exchanges reels)
- Diagnostic Memory (anti-regression)
"""

import asyncio
import json
import logging
import time
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import des nouveaux modules
sys.path.insert(0, '/opt/smartorder-pro/updates')
from UPDATE_risk_management_v2.1_20251031 import RiskManager
from UPDATE_technical_indicators_v2.1_20251031 import TechnicalIndicators
from UPDATE_ccxt_integration_v2.1_20251031 import CCXTManager
from UPDATE_diagnostic_memory_v2.1_20251031 import DiagnosticMemory

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
    """Executeur de strategies de trading avec modules integres"""
    
    def __init__(self):
        self.running = False
        self.strategy_threads = {}
        self.strategies_data = {}
        self.exchanges_data = {}
        self.reload_interval = 10
        
        # Nouveaux modules v2.1
        self.risk_manager = RiskManager()
        self.technical_indicators = TechnicalIndicators()
        self.ccxt_manager = CCXTManager()
        self.diagnostic = DiagnosticMemory()
        
        logger.info("🚀 Strategy Executor v2.1 initialise avec modules avances")
        
    def load_strategies_config(self) -> Dict:
        """Charge la configuration des strategies"""
        try:
            with open(STRATEGIES_FILE, 'r') as f:
                data = json.load(f)
                logger.debug(f"Strategies chargees: {len(data.get('spot', []))} SPOT, "
                           f"{len(data.get('futures', []))} FUTURES, "
                           f"{len(data.get('hybride', []))} HYBRIDE")
                return data
        except Exception as e:
            logger.error(f"Erreur chargement strategies: {e}")
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
        """Recupere toutes les strategies activees"""
        enabled = []
        strategies = self.load_strategies_config()
        
        for mode in ['spot', 'futures', 'hybride']:
            for strategy in strategies.get(mode, []):
                if strategy.get('enabled', False):
                    strategy['mode'] = mode
                    enabled.append(strategy)
        
        return enabled
    
    def get_primary_exchange(self) -> Optional[str]:
        """Recupere l'exchange primaire actif"""
        exchanges = self.load_exchanges_config()
        
        for name, info in exchanges.items():
            if info.get('primary') and info.get('connected'):
                return name
        
        for name, info in exchanges.items():
            if info.get('connected'):
                return name
        
        return None
    
    def execute_strategy(self, strategy: Dict, exchange: str):
        """Execute une strategie de trading avec analyse technique"""
        strategy_id = strategy['id']
        strategy_name = strategy['name']
        mode = strategy.get('mode', 'spot')
        
        logger.info(f"🚀 Demarrage strategie: {strategy_name} ({mode.upper()}) sur {exchange}")
        
        iteration = 0
        
        try:
            while self.running and strategy_id in self.strategy_threads:
                iteration += 1
                
                # Recuperer prix via CCXT
                symbol = "BTC/USDT"  # TODO: rendre configurable
                ticker = self.ccxt_manager.get_ticker(exchange, symbol)
                
                if not ticker:
                    logger.warning(f"[{strategy_name}] Impossible de recuperer ticker")
                    time.sleep(5)
                    continue
                
                current_price = ticker['last']
                
                # Recuperer historique pour analyse technique
                ohlcv = self.ccxt_manager.get_ohlcv(exchange, symbol, '1h', 100)
                
                if ohlcv and len(ohlcv) >= 50:
                    prices = [candle[4] for candle in ohlcv]  # Close prices
                    
                    # Analyse technique
                    analysis = self.technical_indicators.analyze_market(prices)
                    
                    logger.info(f"[{strategy_name}] Prix: ${current_price:.2f} | "
                              f"RSI: {analysis.get('rsi')} | "
                              f"Signal: {analysis.get('signal')}")
                    
                    # Decision de trading basee sur analyse
                    if analysis.get('signal') == 'BUY' and iteration % 30 == 0:
                        # Valider avec Risk Manager
                        amount = 0.001  # TODO: rendre configurable
                        validation = self.risk_manager.validate_trade(
                            symbol, 'BUY', amount, current_price
                        )
                        
                        if validation['valid']:
                            logger.info(f"[{strategy_name}] 📊 Signal BUY valide - "
                                      f"SL: ${validation['stop_loss']:.2f} | "
                                      f"TP: ${validation['take_profit']:.2f}")
                            
                            # TODO: Placer ordre reel en mode LIVE
                            # order = self.ccxt_manager.place_order(...)
                        else:
                            logger.warning(f"[{strategy_name}] ⚠️ Trade rejete: {validation['reasons']}")
                    
                    elif analysis.get('signal') == 'SELL' and iteration % 30 == 0:
                        logger.info(f"[{strategy_name}] 📉 Signal SELL detecte")
                
                # Attendre avant prochaine iteration
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"[{strategy_name}] ❌ Erreur: {e}", exc_info=True)
            self.diagnostic.record_anomaly(strategy_name, str(e), "error")
        finally:
            logger.info(f"[{strategy_name}] ⏹️  Arret strategie")
    
    def start_strategy(self, strategy: Dict, exchange: str):
        """Lance une strategie dans un thread separe"""
        strategy_id = strategy['id']
        
        if strategy_id in self.strategy_threads:
            logger.warning(f"Strategie {strategy['name']} deja en cours")
            return
        
        thread = threading.Thread(
            target=self.execute_strategy,
            args=(strategy, exchange),
            daemon=True
        )
        thread.start()
        self.strategy_threads[strategy_id] = thread
        
        logger.info(f"✅ Strategie {strategy['name']} lancee (Thread ID: {thread.ident})")
    
    def stop_strategy(self, strategy_id: str):
        """Arrete une strategie"""
        if strategy_id in self.strategy_threads:
            del self.strategy_threads[strategy_id]
            logger.info(f"🛑 Arret demande pour strategie {strategy_id}")
    
    def sync_strategies(self):
        """Synchronise les strategies en cours avec la config"""
        enabled_strategies = self.get_enabled_strategies()
        enabled_ids = {s['id'] for s in enabled_strategies}
        running_ids = set(self.strategy_threads.keys())
        
        # Arreter strategies qui ne sont plus enabled
        to_stop = running_ids - enabled_ids
        for strategy_id in to_stop:
            self.stop_strategy(strategy_id)
        
        # Demarrer nouvelles strategies enabled
        exchange = self.get_primary_exchange()
        if not exchange:
            logger.warning("⚠️  Aucun exchange actif - strategies en attente")
            return
        
        # Connecter exchange via CCXT si pas deja fait
        if exchange not in self.ccxt_manager.exchanges:
            exchanges_config = self.load_exchanges_config()
            if exchange in exchanges_config:
                self.ccxt_manager.connect_exchange(exchange, exchanges_config[exchange])
        
        to_start = enabled_ids - running_ids
        for strategy in enabled_strategies:
            if strategy['id'] in to_start:
                self.start_strategy(strategy, exchange)
    
    def run(self):
        """Boucle principale d'execution"""
        logger.info("=" * 80)
        logger.info("🎯 STRATEGY EXECUTOR v2.1 - SmartOrder PRO AI")
        logger.info("=" * 80)
        logger.info(f"Demarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Config: {STRATEGIES_FILE}")
        logger.info(f"Logs: {LOG_DIR / 'strategy_executor.log'}")
        logger.info(f"Risk Management: ACTIVE")
        logger.info(f"Technical Indicators: ACTIVE")
        logger.info(f"CCXT Integration: ACTIVE")
        logger.info(f"Diagnostic Memory: ACTIVE")
        logger.info("=" * 80)
        
        self.running = True
        
        try:
            while self.running:
                # Synchroniser strategies
                self.sync_strategies()
                
                # Update diagnostic
                self.diagnostic.update_check()
                
                # Afficher statut
                enabled = self.get_enabled_strategies()
                running = len(self.strategy_threads)
                
                if running > 0:
                    logger.info(f"📊 Statut: {running} strategie(s) en cours "
                              f"({len(enabled)} activees)")
                else:
                    logger.info(f"⏸️  Aucune strategie en cours ({len(enabled)} activees)")
                
                # Attendre avant prochaine sync
                time.sleep(self.reload_interval)
                
        except KeyboardInterrupt:
            logger.info("\\n⚠️  Interruption utilisateur (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
            self.diagnostic.record_anomaly("strategy_executor", str(e), "critical")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Arret propre du systeme"""
        logger.info("🛑 Arret du Strategy Executor...")
        self.running = False
        
        # Attendre que tous les threads se terminent
        for strategy_id, thread in list(self.strategy_threads.items()):
            logger.info(f"  Attente arret: {strategy_id}")
            thread.join(timeout=5)
        
        logger.info("✅ Arret complet")
        logger.info("=" * 80)


def main():
    """Point d'entree principal"""
    executor = StrategyExecutor()
    
    try:
        executor.run()
    except Exception as e:
        logger.error(f"Erreur critique: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
'''
    
    return integrated_code

def deploy_integrated_executor():
    """Deploie la version integree"""
    
    print("🔄 INTEGRATION STRATEGY EXECUTOR v2.1")
    print("=" * 60)
    
    # 1. Backup
    backup_file = create_backup()
    
    # 2. Creer version integree
    print("📝 Creation version integree...")
    integrated_code = create_integrated_executor()
    
    # 3. Ecrire nouveau fichier
    with open(STRATEGY_EXECUTOR, 'w') as f:
        f.write(integrated_code)
    
    print(f"✅ Strategy Executor v2.1 deploye")
    print(f"📁 Original sauvegarde: {backup_file}")
    print(f"📄 Nouveau fichier: {STRATEGY_EXECUTOR}")
    print("=" * 60)
    print("\n✅ Integration complete - pret pour redemarrage service")

if __name__ == "__main__":
    deploy_integrated_executor()
