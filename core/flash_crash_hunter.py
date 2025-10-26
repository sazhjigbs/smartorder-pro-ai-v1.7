"""
SmartOrder PRO - Flash Crash Hunter Module
Détecte et profite des crashs éclair (flash crashes) en temps réel
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque

LOG = logging.getLogger("flash_crash_hunter")
LOG.setLevel(logging.INFO)

class FlashCrashHunter:
    """
    Détecte les flash crashes et place des ordres d'achat automatiques
    
    Flash Crash = Chute brutale du prix (-3% à -10%) en moins de 1 minute
    suivie d'un rebond rapide
    
    Stratégie:
    1. Surveille les variations de prix toutes les 5 secondes
    2. Détecte chute > 5% en < 60 secondes
    3. Vérifie que c'est pas un crash général (market-wide)
    4. Achète immédiatement
    5. Place TP à +2-3% et SL à -1%
    6. Profit en 2-10 minutes
    
    ROI attendu: +2-5% par flash crash
    Fréquence: 2-5 fois par mois
    """
    
    def __init__(self, window_size: int = 60):
        """
        Initialize Flash Crash Hunter
        
        Args:
            window_size: Fenêtre de détection en secondes (défaut: 60s)
        """
        self.window_size = window_size
        self.price_history = {}  # {symbol: deque([{price, timestamp}])}
        self.detected_crashes = {}  # {symbol: {timestamp, drop_pct, executed}}
        self.is_active = True
        
        # Paramètres de détection
        self.min_drop_pct = 3.0  # Minimum -3% pour déclencher
        self.max_drop_pct = 15.0  # Maximum -15% (au-delà = suspect)
        self.recovery_time_max = 600  # 10 minutes max pour rebond
        
        # Paramètres trading
        self.tp_pct = 2.5  # Take Profit +2.5%
        self.sl_pct = 1.0  # Stop Loss -1%
        
        # Stats
        self.stats = {
            'total_detected': 0,
            'total_traded': 0,
            'wins': 0,
            'losses': 0,
            'total_profit_usdt': 0.0
        }
        
        LOG.info("FlashCrashHunter initialized")
    
    def add_price_tick(self, symbol: str, price: float, timestamp: Optional[float] = None):
        """
        Ajoute un tick de prix à l'historique
        
        Args:
            symbol: Symbole du coin (ex: 'BTCUSDT')
            price: Prix actuel
            timestamp: Timestamp Unix (optionnel, now par défaut)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Initialiser l'historique si nécessaire
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=100)
        
        # Ajouter le tick
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp
        })
        
        # Nettoyer les vieux ticks (> window_size)
        self._cleanup_old_ticks(symbol, timestamp)
    
    def _cleanup_old_ticks(self, symbol: str, current_time: float):
        """Supprime les ticks trop anciens"""
        if symbol not in self.price_history:
            return
        
        cutoff_time = current_time - self.window_size
        history = self.price_history[symbol]
        
        # Supprimer les ticks anciens
        while history and history[0]['timestamp'] < cutoff_time:
            history.popleft()
    
    def detect_flash_crash(self, symbol: str) -> Optional[Dict]:
        """
        Détecte un flash crash sur un symbole
        
        Returns:
            Dict avec infos du crash si détecté, None sinon
        """
        if symbol not in self.price_history:
            return None
        
        history = self.price_history[symbol]
        
        if len(history) < 2:
            return None
        
        # Prix actuel et prix le plus haut dans la fenêtre
        current_tick = history[-1]
        current_price = current_tick['price']
        current_time = current_tick['timestamp']
        
        # Trouver le prix le plus haut dans les dernières 60s
        max_price = max([tick['price'] for tick in history])
        max_tick = [t for t in history if t['price'] == max_price][0]
        
        # Calculer la chute
        drop_pct = ((max_price - current_price) / max_price) * 100
        time_elapsed = current_time - max_tick['timestamp']
        
        # Vérifier les critères de flash crash
        is_flash_crash = (
            drop_pct >= self.min_drop_pct and
            drop_pct <= self.max_drop_pct and
            time_elapsed <= self.window_size
        )
        
        if is_flash_crash:
            crash_data = {
                'symbol': symbol,
                'drop_pct': drop_pct,
                'max_price': max_price,
                'current_price': current_price,
                'time_elapsed': time_elapsed,
                'timestamp': current_time
            }
            
            # Vérifier si déjà détecté récemment (éviter doublons)
            if not self._is_duplicate_detection(symbol, current_time):
                self.stats['total_detected'] += 1
                self.detected_crashes[symbol] = crash_data
                
                LOG.warning(f"🚨 FLASH CRASH DETECTED: {symbol} "
                          f"-{drop_pct:.2f}% in {time_elapsed:.0f}s "
                          f"({max_price} → {current_price})")
                
                return crash_data
        
        return None
    
    def _is_duplicate_detection(self, symbol: str, current_time: float) -> bool:
        """Vérifie si c'est un doublon de détection récente"""
        if symbol not in self.detected_crashes:
            return False
        
        last_detection = self.detected_crashes[symbol]
        time_since = current_time - last_detection.get('timestamp', 0)
        
        # Si détection < 5 minutes = doublon
        return time_since < 300
    
    def should_trade(self, crash_data: Dict, market_condition: str = "NORMAL") -> Tuple[bool, str]:
        """
        Détermine si on doit trader ce flash crash
        
        Args:
            crash_data: Données du crash détecté
            market_condition: NORMAL, PANIC, CRASH_GENERAL
            
        Returns:
            (should_trade, reason)
        """
        symbol = crash_data['symbol']
        drop_pct = crash_data['drop_pct']
        
        # Critère 1: Pas de crash général du marché
        if market_condition == "CRASH_GENERAL":
            reason = f"Market-wide crash detected, skipping {symbol}"
            LOG.warning(reason)
            return False, reason
        
        # Critère 2: Chute dans la plage acceptable
        if drop_pct > self.max_drop_pct:
            reason = f"Drop too large ({drop_pct:.1f}%), might be real crash"
            LOG.warning(reason)
            return False, reason
        
        # Critère 3: Vérifier si pas déjà tradé
        if crash_data.get('executed', False):
            return False, "Already executed"
        
        # Critère 4: Liquidité suffisante (TODO: vérifier volume)
        # Pour l'instant on assume OK
        
        # ✅ Tous les critères OK
        reason = f"Flash crash validated: {symbol} -{drop_pct:.1f}%"
        LOG.info(reason)
        return True, reason
    
    def calculate_entry(self, crash_data: Dict) -> Dict:
        """
        Calcule les paramètres d'entrée pour le trade
        
        Returns:
            Dict avec entry_price, tp_price, sl_price, position_size
        """
        current_price = crash_data['current_price']
        symbol = crash_data['symbol']
        
        # Prix d'entrée = prix actuel (immédiat)
        entry_price = current_price
        
        # Take Profit = +2.5% du prix d'entrée
        tp_price = entry_price * (1 + self.tp_pct / 100)
        
        # Stop Loss = -1% du prix d'entrée
        sl_price = entry_price * (1 - self.sl_pct / 100)
        
        return {
            'symbol': symbol,
            'side': 'BUY',
            'entry_price': round(entry_price, 2),
            'tp_price': round(tp_price, 2),
            'sl_price': round(sl_price, 2),
            'expected_profit_pct': self.tp_pct,
            'max_loss_pct': self.sl_pct
        }
    
    def execute_flash_crash_trade(self, crash_data: Dict, capital: float) -> Dict:
        """
        Execute un trade de flash crash
        
        Args:
            crash_data: Données du crash
            capital: Capital à utiliser en USDT
            
        Returns:
            Résultat de l'exécution
        """
        try:
            entry_params = self.calculate_entry(crash_data)
            
            # TODO: Intégration avec Bybit API
            # Pour l'instant, simulation
            
            result = {
                'success': True,
                'type': 'flash_crash_recovery',
                **entry_params,
                'capital_usdt': capital,
                'quantity': capital / entry_params['entry_price'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Marquer comme exécuté
            crash_data['executed'] = True
            self.stats['total_traded'] += 1
            
            LOG.info(f"✅ Flash crash trade executed: {entry_params['symbol']} "
                    f"BUY @ {entry_params['entry_price']} "
                    f"TP: {entry_params['tp_price']} SL: {entry_params['sl_price']}")
            
            return result
            
        except Exception as e:
            LOG.error(f"Flash crash trade failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_recovery(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Vérifie si le prix a rebondi après un flash crash
        
        Returns:
            'TP_HIT' | 'SL_HIT' | 'WAITING' | None
        """
        if symbol not in self.detected_crashes:
            return None
        
        crash_data = self.detected_crashes[symbol]
        
        if not crash_data.get('executed', False):
            return None
        
        entry_price = crash_data['current_price']
        tp_price = entry_price * (1 + self.tp_pct / 100)
        sl_price = entry_price * (1 - self.sl_pct / 100)
        
        # Check TP hit
        if current_price >= tp_price:
            LOG.info(f"✅ TP HIT: {symbol} @ {current_price} (target: {tp_price})")
            self.stats['wins'] += 1
            self.stats['total_profit_usdt'] += (current_price - entry_price) / entry_price * 100
            return 'TP_HIT'
        
        # Check SL hit
        if current_price <= sl_price:
            LOG.warning(f"❌ SL HIT: {symbol} @ {current_price} (stop: {sl_price})")
            self.stats['losses'] += 1
            self.stats['total_profit_usdt'] -= (entry_price - current_price) / entry_price * 100
            return 'SL_HIT'
        
        return 'WAITING'
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du module"""
        win_rate = 0.0
        if self.stats['total_traded'] > 0:
            win_rate = (self.stats['wins'] / self.stats['total_traded']) * 100
        
        return {
            **self.stats,
            'win_rate': round(win_rate, 1),
            'avg_profit_per_trade': round(
                self.stats['total_profit_usdt'] / max(1, self.stats['total_traded']), 2
            )
        }


# Instance globale
_flash_crash_hunter = None

def get_flash_crash_hunter() -> FlashCrashHunter:
    """Récupère l'instance singleton"""
    global _flash_crash_hunter
    if _flash_crash_hunter is None:
        _flash_crash_hunter = FlashCrashHunter()
    return _flash_crash_hunter


if __name__ == "__main__":
    # Test du module
    print("=" * 60)
    print("Flash Crash Hunter - Test")
    print("=" * 60)
    
    hunter = FlashCrashHunter()
    
    # Simulation d'un flash crash
    symbol = "BTCUSDT"
    base_time = time.time()
    
    # Prix stable autour de 67000
    for i in range(10):
        hunter.add_price_tick(symbol, 67000 + (i % 3) * 10, base_time + i)
    
    print(f"\n📊 Historique initial: {len(hunter.price_history[symbol])} ticks")
    
    # Soudainement, crash de -6%
    crash_price = 67000 * 0.94  # -6%
    hunter.add_price_tick(symbol, crash_price, base_time + 15)
    
    # Détection
    crash_data = hunter.detect_flash_crash(symbol)
    
    if crash_data:
        print(f"\n🚨 Flash crash détecté!")
        print(f"   Symbol: {crash_data['symbol']}")
        print(f"   Drop: -{crash_data['drop_pct']:.2f}%")
        print(f"   Prix: {crash_data['max_price']} → {crash_data['current_price']}")
        print(f"   Temps: {crash_data['time_elapsed']:.0f}s")
        
        # Validation
        should_trade, reason = hunter.should_trade(crash_data, "NORMAL")
        print(f"\n✅ Should trade: {should_trade}")
        print(f"   Reason: {reason}")
        
        if should_trade:
            # Calcul entrée
            entry = hunter.calculate_entry(crash_data)
            print(f"\n💰 Entry params:")
            print(f"   Entry: {entry['entry_price']}")
            print(f"   TP: {entry['tp_price']} (+{entry['expected_profit_pct']}%)")
            print(f"   SL: {entry['sl_price']} (-{entry['max_loss_pct']}%)")
            
            # Execution
            result = hunter.execute_flash_crash_trade(crash_data, 100.0)
            print(f"\n✅ Trade executed: {result['success']}")
    
    # Stats
    stats = hunter.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Detected: {stats['total_detected']}")
    print(f"   Traded: {stats['total_traded']}")
    print(f"   Win rate: {stats['win_rate']}%")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
