"""
SmartOrder PRO - Whale Tracker Module
Détecte et suit les mouvements des gros portefeuilles (whales)
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque

LOG = logging.getLogger("whale_tracker")
LOG.setLevel(logging.INFO)

class WhaleTracker:
    """
    Détecte les ordres et mouvements de whales
    
    Whale = Transaction/Ordre > seuil significatif
    
    Indicateurs:
    1. Large Orders: Ordres > $100k
    2. Volume Spikes: Volume 3x+ supérieur à la moyenne
    3. Unusual Activity: Accumulation/Distribution patterns
    4. Wallet Movements: Transfers vers/depuis exchanges
    
    Trading Logic:
    - Whale achète = Signal BUY (suivre la baleine)
    - Whale vend = Signal SELL (sortir avant le dump)
    - Accumulation = Signal BUY (position long-term)
    - Distribution = Signal SELL (top proche)
    """
    
    def __init__(self, whale_threshold_usdt: float = 100000.0):
        """
        Initialize Whale Tracker
        
        Args:
            whale_threshold_usdt: Seuil pour considérer une transaction comme "whale"
        """
        self.whale_threshold = whale_threshold_usdt
        
        # Historique des transactions
        self.whale_transactions = {}  # {symbol: deque([transaction])}
        
        # Volume historique pour détection de spikes
        self.volume_history = {}  # {symbol: deque([volume])}
        
        # Patterns détectés
        self.detected_patterns = {}  # {symbol: {pattern, timestamp}}
        
        # Stats
        self.stats = {
            'total_whale_txs': 0,
            'total_buy_volume': 0.0,
            'total_sell_volume': 0.0,
            'patterns_detected': 0
        }
        
        LOG.info(f"WhaleTracker initialized (threshold: ${whale_threshold_usdt:,.0f})")
    
    def add_transaction(self, symbol: str, transaction: Dict):
        """
        Ajoute une transaction à l'historique
        
        Args:
            transaction: {
                'timestamp': float,
                'price': float,
                'quantity': float,
                'value_usdt': float,
                'side': 'BUY' | 'SELL'
            }
        """
        if symbol not in self.whale_transactions:
            self.whale_transactions[symbol] = deque(maxlen=100)
        
        # Vérifier si c'est une whale transaction
        value = transaction['value_usdt']
        
        if value >= self.whale_threshold:
            transaction['is_whale'] = True
            self.stats['total_whale_txs'] += 1
            
            if transaction['side'] == 'BUY':
                self.stats['total_buy_volume'] += value
            else:
                self.stats['total_sell_volume'] += value
            
            LOG.warning(f"🐋 WHALE DETECTED: {symbol} {transaction['side']} "
                       f"${value:,.0f} @ {transaction['price']}")
        else:
            transaction['is_whale'] = False
        
        self.whale_transactions[symbol].append(transaction)
    
    def add_volume_tick(self, symbol: str, volume: float, timestamp: Optional[float] = None):
        """
        Ajoute un tick de volume
        
        Args:
            symbol: Symbole
            volume: Volume en USDT
            timestamp: Timestamp Unix
        """
        if timestamp is None:
            timestamp = time.time()
        
        if symbol not in self.volume_history:
            self.volume_history[symbol] = deque(maxlen=50)
        
        self.volume_history[symbol].append({
            'timestamp': timestamp,
            'volume': volume
        })
    
    def detect_volume_spike(self, symbol: str, current_volume: float) -> Optional[Dict]:
        """
        Détecte un spike de volume anormal
        
        Returns:
            Dict avec infos du spike si détecté, None sinon
        """
        if symbol not in self.volume_history:
            return None
        
        history = list(self.volume_history[symbol])
        
        if len(history) < 10:
            return None
        
        # Calculer volume moyen
        volumes = [h['volume'] for h in history[:-1]]  # Exclure le dernier
        avg_volume = sum(volumes) / len(volumes)
        
        # Spike = volume 3x+ supérieur à la moyenne
        spike_multiplier = current_volume / avg_volume if avg_volume > 0 else 0
        
        if spike_multiplier >= 3.0:
            spike_data = {
                'symbol': symbol,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'spike_multiplier': spike_multiplier,
                'timestamp': time.time()
            }
            
            LOG.warning(f"📊 VOLUME SPIKE: {symbol} {spike_multiplier:.1f}x normal volume")
            
            return spike_data
        
        return None
    
    def detect_accumulation_distribution(self, symbol: str, periods: int = 20) -> Optional[Dict]:
        """
        Détecte les patterns d'accumulation ou distribution
        
        Accumulation = Whales achètent progressivement
        Distribution = Whales vendent progressivement
        
        Returns:
            {'pattern': 'ACCUMULATION' | 'DISTRIBUTION', 'strength': 0-100}
        """
        if symbol not in self.whale_transactions:
            return None
        
        txs = list(self.whale_transactions[symbol])[-periods:]
        
        if len(txs) < 10:
            return None
        
        # Filtrer seulement les whale transactions
        whale_txs = [tx for tx in txs if tx.get('is_whale', False)]
        
        if len(whale_txs) < 3:
            return None
        
        # Calculer ratio buy/sell
        buy_volume = sum(tx['value_usdt'] for tx in whale_txs if tx['side'] == 'BUY')
        sell_volume = sum(tx['value_usdt'] for tx in whale_txs if tx['side'] == 'SELL')
        
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return None
        
        buy_ratio = buy_volume / total_volume
        
        # Accumulation si buy_ratio > 65%
        # Distribution si buy_ratio < 35%
        
        if buy_ratio > 0.65:
            pattern = 'ACCUMULATION'
            strength = min(100, buy_ratio * 120)  # Scale to 0-100
        elif buy_ratio < 0.35:
            pattern = 'DISTRIBUTION'
            strength = min(100, (1 - buy_ratio) * 120)
        else:
            return None
        
        result = {
            'symbol': symbol,
            'pattern': pattern,
            'strength': round(strength, 1),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_ratio': round(buy_ratio * 100, 1),
            'whale_count': len(whale_txs),
            'timestamp': time.time()
        }
        
        # Stocker
        self.detected_patterns[symbol] = result
        self.stats['patterns_detected'] += 1
        
        LOG.warning(f"📈 PATTERN DETECTED: {symbol} {pattern} "
                   f"(strength: {strength:.0f}%, ratio: {buy_ratio*100:.0f}% buy)")
        
        return result
    
    def get_whale_signal(self, symbol: str) -> Dict:
        """
        Génère un signal de trading basé sur l'activité whale
        
        Returns:
            {
                'signal': 'BUY' | 'SELL' | 'NEUTRAL',
                'confidence': 0-100,
                'reason': str,
                'recommendations': {...}
            }
        """
        # Vérifier pattern d'accumulation/distribution
        pattern = self.detect_accumulation_distribution(symbol)
        
        if pattern:
            if pattern['pattern'] == 'ACCUMULATION':
                signal = 'BUY'
                confidence = pattern['strength']
                reason = f"Whale accumulation detected ({pattern['whale_count']} large buyers)"
            else:
                signal = 'SELL'
                confidence = pattern['strength']
                reason = f"Whale distribution detected ({pattern['whale_count']} large sellers)"
        else:
            # Regarder les transactions récentes
            if symbol not in self.whale_transactions:
                return self._neutral_signal(symbol)
            
            recent_txs = list(self.whale_transactions[symbol])[-5:]
            whale_txs = [tx for tx in recent_txs if tx.get('is_whale', False)]
            
            if not whale_txs:
                return self._neutral_signal(symbol)
            
            # Majorité buy ou sell?
            buy_count = sum(1 for tx in whale_txs if tx['side'] == 'BUY')
            sell_count = len(whale_txs) - buy_count
            
            if buy_count > sell_count:
                signal = 'BUY'
                confidence = min(80, (buy_count / len(whale_txs)) * 100)
                reason = f"{buy_count} recent whale buy(s) detected"
            elif sell_count > buy_count:
                signal = 'SELL'
                confidence = min(80, (sell_count / len(whale_txs)) * 100)
                reason = f"{sell_count} recent whale sell(s) detected"
            else:
                return self._neutral_signal(symbol)
        
        # Recommandations
        recommendations = {
            'action': signal,
            'urgency': 'HIGH' if confidence > 70 else 'MEDIUM',
            'position_size': 'NORMAL' if confidence > 60 else 'SMALL',
            'stop_loss': 'TIGHT' if signal == 'SELL' else 'NORMAL'
        }
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': round(confidence, 1),
            'reason': reason,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def _neutral_signal(self, symbol: str) -> Dict:
        """Signal neutre par défaut"""
        return {
            'symbol': symbol,
            'signal': 'NEUTRAL',
            'confidence': 0,
            'reason': 'No significant whale activity detected',
            'recommendations': {
                'action': 'HOLD',
                'urgency': 'LOW',
                'position_size': 'NORMAL',
                'stop_loss': 'NORMAL'
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_whale_summary(self, symbol: str) -> Dict:
        """Résumé de l'activité whale pour un symbole"""
        if symbol not in self.whale_transactions:
            return {}
        
        txs = list(self.whale_transactions[symbol])
        whale_txs = [tx for tx in txs if tx.get('is_whale', False)]
        
        if not whale_txs:
            return {
                'symbol': symbol,
                'whale_count': 0,
                'message': 'No whale activity'
            }
        
        buy_count = sum(1 for tx in whale_txs if tx['side'] == 'BUY')
        sell_count = len(whale_txs) - buy_count
        
        total_buy_volume = sum(tx['value_usdt'] for tx in whale_txs if tx['side'] == 'BUY')
        total_sell_volume = sum(tx['value_usdt'] for tx in whale_txs if tx['side'] == 'SELL')
        
        return {
            'symbol': symbol,
            'whale_count': len(whale_txs),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_buy_volume': round(total_buy_volume, 2),
            'total_sell_volume': round(total_sell_volume, 2),
            'net_volume': round(total_buy_volume - total_sell_volume, 2),
            'dominant_side': 'BUY' if buy_count > sell_count else 'SELL',
            'last_whale_tx': whale_txs[-1] if whale_txs else None
        }
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques globales"""
        return {
            **self.stats,
            'net_whale_volume': round(
                self.stats['total_buy_volume'] - self.stats['total_sell_volume'], 2
            ),
            'buy_sell_ratio': round(
                self.stats['total_buy_volume'] / max(1, self.stats['total_sell_volume']), 2
            )
        }


# Instance globale
_whale_tracker = None

def get_whale_tracker() -> WhaleTracker:
    """Récupère l'instance singleton"""
    global _whale_tracker
    if _whale_tracker is None:
        _whale_tracker = WhaleTracker()
    return _whale_tracker


if __name__ == "__main__":
    print("=" * 60)
    print("Whale Tracker - Test")
    print("=" * 60)
    
    tracker = WhaleTracker(whale_threshold_usdt=100000.0)
    
    symbol = "BTCUSDT"
    
    # Simuler des transactions normales
    print(f"\n📊 Ajout de transactions normales...")
    for i in range(10):
        tracker.add_transaction(symbol, {
            'timestamp': time.time(),
            'price': 67000.0,
            'quantity': 0.5,
            'value_usdt': 33500.0,
            'side': 'BUY' if i % 2 == 0 else 'SELL'
        })
    
    # Simuler des whale transactions (accumulation)
    print(f"\n🐋 Simulation de whale accumulation...")
    for i in range(5):
        tracker.add_transaction(symbol, {
            'timestamp': time.time() + i,
            'price': 67000.0,
            'quantity': 10.0,
            'value_usdt': 670000.0,
            'side': 'BUY'
        })
    
    # Détecter pattern
    print(f"\n🔍 Détection de patterns...")
    pattern = tracker.detect_accumulation_distribution(symbol)
    
    if pattern:
        print(f"   Pattern: {pattern['pattern']}")
        print(f"   Strength: {pattern['strength']:.1f}%")
        print(f"   Buy ratio: {pattern['buy_ratio']:.1f}%")
        print(f"   Whale count: {pattern['whale_count']}")
    
    # Signal
    print(f"\n💡 Génération du signal...")
    signal = tracker.get_whale_signal(symbol)
    
    print(f"   Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']:.1f}%")
    print(f"   Reason: {signal['reason']}")
    print(f"   Action: {signal['recommendations']['action']}")
    print(f"   Urgency: {signal['recommendations']['urgency']}")
    
    # Summary
    print(f"\n📊 Whale Summary:")
    summary = tracker.get_whale_summary(symbol)
    print(f"   Whale transactions: {summary['whale_count']}")
    print(f"   Buy/Sell: {summary['buy_count']}/{summary['sell_count']}")
    print(f"   Net volume: ${summary['net_volume']:,.0f}")
    print(f"   Dominant side: {summary['dominant_side']}")
    
    # Stats
    stats = tracker.get_stats()
    print(f"\n📊 Global Stats:")
    print(f"   Total whale txs: {stats['total_whale_txs']}")
    print(f"   Patterns detected: {stats['patterns_detected']}")
    print(f"   Net whale volume: ${stats['net_whale_volume']:,.0f}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
