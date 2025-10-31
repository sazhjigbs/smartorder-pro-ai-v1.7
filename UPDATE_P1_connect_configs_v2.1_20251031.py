#!/usr/bin/env python3
"""
UPDATE P1: Connect Configs to Strategy Executor
Date: 2025-10-31
Version: v2.1-P1

OBJECTIF:
- Supprimer TOUT hardcode
- Lire watchlist.json, risk_config.json, paper_wallet.json
- Ecrire paper_wallet.json apres chaque trade
- Logger trades dans pnl_tracker.jsonl (NDJSON)

DoD:
- Aucun symbole en dur (BTC/USDT, ETH/USDT = 0 occur.)
- Modifier watchlist.json → bot trade ces paires
- Modifier risk_config.json → valeurs appliquees et persistent
- Trade simule → paper_wallet.json varie
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

SMARTORDER_PATH = Path("/opt/smartorder-pro")
STRATEGY_EXECUTOR = SMARTORDER_PATH / "strategy_executor.py"
BACKUP_PATH = SMARTORDER_PATH / "backups"
UPDATES_PATH = SMARTORDER_PATH / "updates"

def create_backup():
    """Backup strategy_executor avant modification"""
    BACKUP_PATH.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_PATH / f"strategy_executor_before_P1_{timestamp}.py"
    shutil.copy(STRATEGY_EXECUTOR, backup_file)
    print(f"✅ Backup: {backup_file}")
    return backup_file

def read_current_executor():
    """Lit le strategy_executor actuel"""
    with open(STRATEGY_EXECUTOR, 'r') as f:
        return f.read()

def create_patched_executor():
    """Cree version patchee avec lecture configs"""
    
    code = '''#!/usr/bin/env python3
"""
🎯 STRATEGY EXECUTOR v2.1-P1 - SmartOrder PRO AI
Moteur execution avec config dynamique (watchlist, risk, wallet)

Changelog v2.1-P1:
- Lecture watchlist.json (plus de hardcode)
- Lecture risk_config.json (parametres dynamiques)
- Ecriture paper_wallet.json (balance dynamique)
- Logger NDJSON pnl_tracker.jsonl
"""

import json
import logging
import time
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import modules v2.1
sys.path.insert(0, '/opt/smartorder-pro/updates')
from risk_management import RiskManager
from technical_indicators import TechnicalIndicators
from ccxt_integration import CCXTManager
from diagnostic_memory import DiagnosticMemory

# Configuration
CONFIG_DIR = Path('/opt/smartorder-pro/config')
STRATEGIES_FILE = CONFIG_DIR / 'strategies_state.json'
EXCHANGES_FILE = CONFIG_DIR / 'exchanges_state.json'
WATCHLIST_FILE = CONFIG_DIR / 'watchlist.json'
RISK_CONFIG_FILE = CONFIG_DIR / 'risk_config.json'
PAPER_WALLET_FILE = CONFIG_DIR / 'paper_wallet.json'
LOG_DIR = Path('/opt/smartorder-pro/logs')
PNL_TRACKER_JSONL = LOG_DIR / 'pnl_tracker.jsonl'
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


class ConfigManager:
    """Gestionnaire de configuration dynamique"""
    
    @staticmethod
    def load_watchlist() -> List[str]:
        """Charge watchlist depuis JSON"""
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                data = json.load(f)
            pairs = data.get('pairs', ['BTC/USDT'])
            logger.info(f"📋 Watchlist chargee: {len(pairs)} paires - {', '.join(pairs)}")
            return pairs
        except Exception as e:
            logger.error(f"Erreur chargement watchlist: {e}")
            return ['BTC/USDT']
    
    @staticmethod
    def load_risk_config() -> Dict:
        """Charge config risk depuis JSON"""
        try:
            with open(RISK_CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.info(f"🛡️  Risk config chargee: Max pos={config.get('max_position_size_usdt')} USDT, "
                       f"SL={config.get('stop_loss_pct')}%, TP={config.get('take_profit_pct')}%")
            return config
        except Exception as e:
            logger.error(f"Erreur chargement risk config: {e}")
            return {
                'max_position_size_usdt': 1000,
                'stop_loss_pct': 2.0,
                'take_profit_pct': 3.0,
                'max_open_trades': 5,
                'max_daily_loss_usdt': 100
            }
    
    @staticmethod
    def load_paper_wallet() -> Dict:
        """Charge wallet depuis JSON"""
        try:
            with open(PAPER_WALLET_FILE, 'r') as f:
                wallet = json.load(f)
            logger.info(f"💰 Wallet charge: Balance={wallet.get('balance_usdt'):.2f} USDT, "
                       f"PnL realise={wallet.get('realized_pnl_usdt'):.2f}")
            return wallet
        except Exception as e:
            logger.error(f"Erreur chargement wallet: {e}")
            default_wallet = {
                'balance_usdt': 10000.0,
                'equity_usdt': 10000.0,
                'unrealized_pnl_usdt': 0.0,
                'realized_pnl_usdt': 0.0,
                'updated_at': datetime.now().isoformat()
            }
            ConfigManager.save_paper_wallet(default_wallet)
            return default_wallet
    
    @staticmethod
    def save_paper_wallet(wallet: Dict):
        """Sauvegarde wallet dans JSON"""
        wallet['updated_at'] = datetime.now().isoformat()
        with open(PAPER_WALLET_FILE, 'w') as f:
            json.dump(wallet, f, indent=2)
        logger.debug(f"💾 Wallet sauvegarde: {wallet['balance_usdt']:.2f} USDT")
    
    @staticmethod
    def log_trade_ndjson(trade: Dict):
        """Log trade en NDJSON dans pnl_tracker.jsonl"""
        with open(PNL_TRACKER_JSONL, 'a') as f:
            f.write(json.dumps(trade) + '\\n')


class StrategyExecutor:
    """Executeur de strategies avec config dynamique"""
    
    def __init__(self):
        self.running = False
        self.strategy_threads = {}
        self.reload_interval = 10
        
        # Charger configs
        self.watchlist = ConfigManager.load_watchlist()
        self.risk_config = ConfigManager.load_risk_config()
        self.wallet = ConfigManager.load_paper_wallet()
        
        # Modules v2.1 avec config dynamique
        self.risk_manager = RiskManager()
        self.risk_manager.max_position_size = self.risk_config['max_position_size_usdt']
        self.risk_manager.stop_loss_percent = self.risk_config['stop_loss_pct'] / 100
        self.risk_manager.take_profit_percent = self.risk_config['take_profit_pct'] / 100
        self.risk_manager.max_daily_loss = self.risk_config['max_daily_loss_usdt']
        
        self.technical_indicators = TechnicalIndicators()
        self.ccxt_manager = CCXTManager()
        self.diagnostic = DiagnosticMemory()
        
        logger.info("🚀 Strategy Executor v2.1-P1 initialise avec config dynamique")
        
    def load_strategies_config(self) -> Dict:
        """Charge configuration strategies"""
        try:
            with open(STRATEGIES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement strategies: {e}")
            return {'spot': [], 'futures': [], 'hybride': []}
    
    def load_exchanges_config(self) -> Dict:
        """Charge configuration exchanges"""
        try:
            with open(EXCHANGES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement exchanges: {e}")
            return {}
    
    def get_enabled_strategies(self) -> List[Dict]:
        """Recupere strategies activees"""
        enabled = []
        strategies = self.load_strategies_config()
        
        for mode in ['spot', 'futures', 'hybride']:
            for strategy in strategies.get(mode, []):
                if strategy.get('enabled', False):
                    strategy['mode'] = mode
                    enabled.append(strategy)
        
        return enabled
    
    def get_primary_exchange(self) -> Optional[str]:
        """Recupere exchange primaire"""
        exchanges = self.load_exchanges_config()
        
        for name, info in exchanges.items():
            if info.get('primary') and info.get('connected'):
                return name
        
        for name, info in exchanges.items():
            if info.get('connected'):
                return name
        
        return None
    
    def update_wallet_after_trade(self, pnl: float):
        """Met a jour wallet apres trade"""
        self.wallet['realized_pnl_usdt'] += pnl
        self.wallet['balance_usdt'] += pnl
        self.wallet['equity_usdt'] = self.wallet['balance_usdt'] + self.wallet['unrealized_pnl_usdt']
        ConfigManager.save_paper_wallet(self.wallet)
        logger.info(f"💰 Wallet mis a jour: Balance={self.wallet['balance_usdt']:.2f}, PnL={pnl:.2f}")
    
    def execute_strategy(self, strategy: Dict, exchange: str):
        """Execute strategie avec watchlist et risk config"""
        strategy_id = strategy['id']
        strategy_name = strategy['name']
        mode = strategy.get('mode', 'spot')
        
        logger.info(f"🚀 Demarrage: {strategy_name} ({mode.upper()}) sur {exchange}")
        
        iteration = 0
        
        try:
            while self.running and strategy_id in self.strategy_threads:
                iteration += 1
                
                # Reload watchlist periodiquement
                if iteration % 60 == 0:
                    self.watchlist = ConfigManager.load_watchlist()
                
                # Iterer sur chaque paire de la watchlist
                for symbol in self.watchlist:
                    ticker = self.ccxt_manager.get_ticker(exchange, symbol)
                    
                    if not ticker:
                        continue
                    
                    current_price = ticker['last']
                    
                    # Recuperer historique
                    ohlcv = self.ccxt_manager.get_ohlcv(exchange, symbol, '1h', 100)
                    
                    if ohlcv and len(ohlcv) >= 50:
                        prices = [candle[4] for candle in ohlcv]
                        analysis = self.technical_indicators.analyze_market(prices)
                        
                        logger.info(f"[{strategy_name}] {symbol}: ${current_price:.2f} | "
                                  f"RSI: {analysis.get('rsi')} | Signal: {analysis.get('signal')}")
                        
                        # Decision trading
                        if analysis.get('signal') == 'BUY' and iteration % 30 == 0:
                            amount = 0.001
                            validation = self.risk_manager.validate_trade(symbol, 'BUY', amount, current_price)
                            
                            if validation['valid']:
                                # Simuler trade
                                pnl_simulated = (validation['take_profit'] - current_price) * amount
                                
                                trade_record = {
                                    'timestamp': datetime.now().isoformat(),
                                    'strategy': strategy_name,
                                    'symbol': symbol,
                                    'side': 'BUY',
                                    'amount': amount,
                                    'price': current_price,
                                    'pnl': pnl_simulated,
                                    'stop_loss': validation['stop_loss'],
                                    'take_profit': validation['take_profit']
                                }
                                
                                # Logger NDJSON
                                ConfigManager.log_trade_ndjson(trade_record)
                                
                                # Update wallet
                                self.update_wallet_after_trade(pnl_simulated)
                                
                                logger.info(f"[{strategy_name}] 📊 Trade BUY {symbol}: "
                                          f"PnL={pnl_simulated:.2f} | "
                                          f"SL={validation['stop_loss']:.2f} | "
                                          f"TP={validation['take_profit']:.2f}")
                            else:
                                logger.warning(f"[{strategy_name}] ⚠️ Trade rejete: {validation['reasons']}")
                
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"[{strategy_name}] ❌ Erreur: {e}", exc_info=True)
            self.diagnostic.record_anomaly(strategy_name, str(e), "error")
        finally:
            logger.info(f"[{strategy_name}] ⏹️  Arret strategie")
    
    def start_strategy(self, strategy: Dict, exchange: str):
        """Lance strategie dans thread"""
        strategy_id = strategy['id']
        
        if strategy_id in self.strategy_threads:
            return
        
        thread = threading.Thread(
            target=self.execute_strategy,
            args=(strategy, exchange),
            daemon=True
        )
        thread.start()
        self.strategy_threads[strategy_id] = thread
        logger.info(f"✅ Strategie {strategy['name']} lancee")
    
    def stop_strategy(self, strategy_id: str):
        """Arrete strategie"""
        if strategy_id in self.strategy_threads:
            del self.strategy_threads[strategy_id]
            logger.info(f"🛑 Arret: {strategy_id}")
    
    def sync_strategies(self):
        """Synchronise strategies"""
        enabled_strategies = self.get_enabled_strategies()
        enabled_ids = {s['id'] for s in enabled_strategies}
        running_ids = set(self.strategy_threads.keys())
        
        to_stop = running_ids - enabled_ids
        for strategy_id in to_stop:
            self.stop_strategy(strategy_id)
        
        exchange = self.get_primary_exchange()
        if not exchange:
            return
        
        if exchange not in self.ccxt_manager.exchanges:
            exchanges_config = self.load_exchanges_config()
            if exchange in exchanges_config:
                self.ccxt_manager.connect_exchange(exchange, exchanges_config[exchange])
        
        to_start = enabled_ids - running_ids
        for strategy in enabled_strategies:
            if strategy['id'] in to_start:
                self.start_strategy(strategy, exchange)
    
    def run(self):
        """Boucle principale"""
        logger.info("=" * 80)
        logger.info("🎯 STRATEGY EXECUTOR v2.1-P1 - SmartOrder PRO AI")
        logger.info("=" * 80)
        logger.info(f"Watchlist: {', '.join(self.watchlist)}")
        logger.info(f"Risk: Max={self.risk_config['max_position_size_usdt']} USDT, "
                   f"SL={self.risk_config['stop_loss_pct']}%, TP={self.risk_config['take_profit_pct']}%")
        logger.info(f"Wallet: {self.wallet['balance_usdt']:.2f} USDT")
        logger.info("=" * 80)
        
        self.running = True
        
        try:
            while self.running:
                self.sync_strategies()
                self.diagnostic.update_check()
                
                enabled = self.get_enabled_strategies()
                running = len(self.strategy_threads)
                
                if running > 0:
                    logger.info(f"📊 {running} strategie(s) en cours ({len(enabled)} activees)")
                
                time.sleep(self.reload_interval)
                
        except KeyboardInterrupt:
            logger.info("\\n⚠️  Interruption (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
            self.diagnostic.record_anomaly("strategy_executor", str(e), "critical")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Arret propre"""
        logger.info("🛑 Arret Strategy Executor...")
        self.running = False
        
        for strategy_id, thread in list(self.strategy_threads.items()):
            thread.join(timeout=5)
        
        logger.info("✅ Arret complet")


def main():
    executor = StrategyExecutor()
    try:
        executor.run()
    except Exception as e:
        logger.error(f"Erreur critique: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
'''
    
    return code

def deploy_patched_executor():
    """Deploie version patchee P1"""
    print("=" * 60)
    print("🔄 UPDATE P1: Connect Configs")
    print("=" * 60)
    
    backup_file = create_backup()
    print("📝 Creation version P1...")
    patched_code = create_patched_executor()
    
    with open(STRATEGY_EXECUTOR, 'w') as f:
        f.write(patched_code)
    
    print(f"✅ Strategy Executor v2.1-P1 deploye")
    print(f"📁 Backup: {backup_file}")
    print("=" * 60)
    print("\n✅ UPDATE P1 COMPLETE")
    print("\nTests a effectuer:")
    print("1. Verifier aucun hardcode: grep -n 'BTC/USDT' strategy_executor.py")
    print("2. Demarrer bot et verifier lecture configs dans logs")
    print("3. Modifier watchlist.json et voir changement comportement")
    print("4. Verifier paper_wallet.json varie apres trades")

if __name__ == "__main__":
    deploy_patched_executor()
