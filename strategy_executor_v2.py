#!/usr/bin/env python3
"""
🎯 STRATEGY EXECUTOR v2 - SmartOrder PRO AI
Avec PnL tracking et positions simulées réalistes
"""

import json
import logging
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import threading

# Configuration
CONFIG_DIR = Path('/opt/smartorder-pro/config')
STRATEGIES_FILE = CONFIG_DIR / 'strategies_state.json'
EXCHANGES_FILE = CONFIG_DIR / 'exchanges_state.json'
WATCHLIST_FILE = CONFIG_DIR / 'watchlist.json'
POSITIONS_FILE = CONFIG_DIR / 'positions.json'
PNL_FILE = CONFIG_DIR / 'pnl_tracker.json'
LOG_DIR = Path('/opt/smartorder-pro/logs')
LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'strategy_executor_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prix simulés (seront remplacés par vrais prix CCXT plus tard)
SIMULATED_PRICES = {
    'BTC/USDT': 43250.00,
    'ETH/USDT': 2280.00
}


class PositionManager:
    """Gestionnaire de positions simulées"""
    
    def __init__(self):
        self.positions = self.load_positions()
        self.pnl_tracker = self.load_pnl()
    
    def load_positions(self) -> List[Dict]:
        """Charge les positions depuis le fichier"""
        try:
            if POSITIONS_FILE.exists():
                with open(POSITIONS_FILE) as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def save_positions(self):
        """Sauvegarde les positions"""
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(self.positions, f, indent=2)
    
    def load_pnl(self) -> Dict:
        """Charge le PnL tracker"""
        try:
            if PNL_FILE.exists():
                with open(PNL_FILE) as f:
                    return json.load(f)
            return {'total_pnl': 0.0, 'trades': [], 'by_strategy': {}}
        except:
            return {'total_pnl': 0.0, 'trades': [], 'by_strategy': {}}
    
    def save_pnl(self):
        """Sauvegarde le PnL"""
        with open(PNL_FILE, 'w') as f:
            json.dump(self.pnl_tracker, f, indent=2)
    
    def get_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel (simulé)"""
        base_price = SIMULATED_PRICES.get(symbol, 1000.0)
        # Varier de +/- 0.5%
        variation = random.uniform(-0.005, 0.005)
        return round(base_price * (1 + variation), 2)
    
    def open_position(self, symbol: str, side: str, amount: float, 
                     entry_price: float, strategy: str) -> Dict:
        """Ouvre une position"""
        position = {
            'id': f'pos_{int(time.time())}_{random.randint(1000, 9999)}',
            'symbol': symbol,
            'side': side,  # 'BUY' ou 'SELL'
            'amount': amount,
            'entry_price': entry_price,
            'current_price': entry_price,
            'pnl': 0.0,
            'pnl_percent': 0.0,
            'strategy': strategy,
            'opened_at': datetime.now().isoformat(),
            'status': 'open'
        }
        
        self.positions.append(position)
        self.save_positions()
        
        logger.info(f"🟢 Position ouverte: {side} {amount} {symbol} @ ${entry_price} "
                   f"(Strategy: {strategy})")
        
        return position
    
    def close_position(self, position_id: str, exit_price: float) -> Dict:
        """Ferme une position"""
        for pos in self.positions:
            if pos['id'] == position_id and pos['status'] == 'open':
                # Calculer PnL
                if pos['side'] == 'BUY':
                    pnl = (exit_price - pos['entry_price']) * pos['amount']
                else:  # SELL
                    pnl = (pos['entry_price'] - exit_price) * pos['amount']
                
                pos['status'] = 'closed'
                pos['exit_price'] = exit_price
                pos['pnl'] = round(pnl, 2)
                pos['closed_at'] = datetime.now().isoformat()
                
                # Mettre à jour total PnL
                self.pnl_tracker['total_pnl'] += pnl
                
                # Tracker par stratégie
                strategy = pos['strategy']
                if strategy not in self.pnl_tracker['by_strategy']:
                    self.pnl_tracker['by_strategy'][strategy] = 0.0
                self.pnl_tracker['by_strategy'][strategy] += pnl
                
                # Ajouter au historique
                self.pnl_tracker['trades'].append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': pos['symbol'],
                    'side': pos['side'],
                    'amount': pos['amount'],
                    'entry': pos['entry_price'],
                    'exit': exit_price,
                    'pnl': pnl,
                    'strategy': strategy
                })
                
                self.save_positions()
                self.save_pnl()
                
                logger.info(f"🔴 Position fermée: {pos['symbol']} @ ${exit_price} | "
                           f"PnL: ${pnl:.2f} | Total PnL: ${self.pnl_tracker['total_pnl']:.2f}")
                
                return pos
        
        return None
    
    def update_open_positions(self):
        """Met à jour le PnL des positions ouvertes"""
        for pos in self.positions:
            if pos['status'] == 'open':
                current_price = self.get_current_price(pos['symbol'])
                pos['current_price'] = current_price
                
                if pos['side'] == 'BUY':
                    pnl = (current_price - pos['entry_price']) * pos['amount']
                else:
                    pnl = (pos['entry_price'] - current_price) * pos['amount']
                
                pos['pnl'] = round(pnl, 2)
                pos['pnl_percent'] = round((pnl / (pos['entry_price'] * pos['amount'])) * 100, 2)
        
        self.save_positions()


class StrategyExecutor:
    """Exécuteur de stratégies avec PnL tracking"""
    
    def __init__(self):
        self.running = False
        self.strategy_threads = {}
        self.position_manager = PositionManager()
        self.reload_interval = 10
    
    def load_watchlist(self) -> List[str]:
        """Charge la watchlist"""
        try:
            with open(WATCHLIST_FILE) as f:
                data = json.load(f)
                return data.get('coins', ['BTC/USDT', 'ETH/USDT'])
        except:
            return ['BTC/USDT', 'ETH/USDT']
    
    def load_strategies_config(self) -> Dict:
        """Charge les stratégies"""
        try:
            with open(STRATEGIES_FILE) as f:
                return json.load(f)
        except:
            return {'spot': [], 'futures': [], 'hybride': []}
    
    def get_enabled_strategies(self) -> List[Dict]:
        """Récupère stratégies activées"""
        enabled = []
        strategies = self.load_strategies_config()
        
        for mode in ['spot', 'futures', 'hybride']:
            for strategy in strategies.get(mode, []):
                if strategy.get('enabled', False):
                    strategy['mode'] = mode
                    enabled.append(strategy)
        
        return enabled
    
    def execute_strategy(self, strategy: Dict):
        """Exécute une stratégie avec trading simulé"""
        strategy_id = strategy['id']
        strategy_name = strategy['name']
        watchlist = self.load_watchlist()
        
        logger.info(f"🚀 {strategy_name} démarre - Trading: {', '.join(watchlist)}")
        
        iteration = 0
        open_positions = {}  # {symbol: position_id}
        
        try:
            while self.running and strategy_id in self.strategy_threads:
                iteration += 1
                
                # Mettre à jour prix positions ouvertes
                if iteration % 5 == 0:
                    self.position_manager.update_open_positions()
                
                # Trading logic simulée
                for symbol in watchlist:
                    current_price = self.position_manager.get_current_price(symbol)
                    
                    # Si pas de position ouverte, ouvrir
                    if symbol not in open_positions:
                        if iteration % 20 == 0:  # Ouvrir position toutes les 20 secondes
                            side = 'BUY' if random.random() > 0.5 else 'SELL'
                            amount = round(random.uniform(0.001, 0.01), 6)
                            
                            pos = self.position_manager.open_position(
                                symbol, side, amount, current_price, strategy_name
                            )
                            open_positions[symbol] = pos['id']
                    
                    # Si position ouverte, décider si fermer
                    elif symbol in open_positions:
                        if iteration % 40 == 0:  # Fermer après 40 secondes
                            self.position_manager.close_position(
                                open_positions[symbol], current_price
                            )
                            del open_positions[symbol]
                
                # Mettre à jour PnL de la stratégie
                if iteration % 10 == 0:
                    total_pnl = self.position_manager.pnl_tracker['total_pnl']
                    logger.info(f"[{strategy_name}] 📊 PnL Global: ${total_pnl:.2f}")
                
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"[{strategy_name}] ❌ Erreur: {e}")
        finally:
            # Fermer toutes les positions ouvertes
            for symbol, pos_id in open_positions.items():
                price = self.position_manager.get_current_price(symbol)
                self.position_manager.close_position(pos_id, price)
            
            logger.info(f"[{strategy_name}] ⏹️  Arrêt")
    
    def start_strategy(self, strategy: Dict):
        """Lance une stratégie"""
        strategy_id = strategy['id']
        
        if strategy_id in self.strategy_threads:
            return
        
        thread = threading.Thread(
            target=self.execute_strategy,
            args=(strategy,),
            daemon=True
        )
        thread.start()
        self.strategy_threads[strategy_id] = thread
        
        logger.info(f"✅ {strategy['name']} lancée")
    
    def stop_strategy(self, strategy_id: str):
        """Arrête une stratégie"""
        if strategy_id in self.strategy_threads:
            del self.strategy_threads[strategy_id]
            logger.info(f"🛑 Stratégie {strategy_id} arrêtée")
    
    def sync_strategies(self):
        """Synchronise stratégies"""
        enabled = self.get_enabled_strategies()
        enabled_ids = {s['id'] for s in enabled}
        running_ids = set(self.strategy_threads.keys())
        
        # Arrêter
        for sid in (running_ids - enabled_ids):
            self.stop_strategy(sid)
        
        # Démarrer
        for strategy in enabled:
            if strategy['id'] in (enabled_ids - running_ids):
                self.start_strategy(strategy)
    
    def run(self):
        """Boucle principale"""
        logger.info("=" * 80)
        logger.info("🎯 STRATEGY EXECUTOR v2 - PnL Tracking ACTIF")
        logger.info("=" * 80)
        logger.info(f"Watchlist: {', '.join(self.load_watchlist())}")
        logger.info(f"PnL Total Initial: ${self.position_manager.pnl_tracker['total_pnl']:.2f}")
        logger.info("=" * 80)
        
        self.running = True
        
        try:
            while self.running:
                self.sync_strategies()
                time.sleep(self.reload_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Ctrl+C - Arrêt")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Arrêt propre"""
        logger.info("🛑 Arrêt...")
        self.running = False
        
        for sid, thread in list(self.strategy_threads.items()):
            thread.join(timeout=5)
        
        final_pnl = self.position_manager.pnl_tracker['total_pnl']
        logger.info(f"💰 PnL Total Final: ${final_pnl:.2f}")
        logger.info("=" * 80)


if __name__ == '__main__':
    executor = StrategyExecutor()
    executor.run()
