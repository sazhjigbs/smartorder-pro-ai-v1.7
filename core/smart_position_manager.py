#!/usr/bin/env python3
"""
🎯 SMART POSITION MANAGER
=========================
by MAIGA ABOUBACAR

Gestion intelligente des positions avec:
- Décisions IA automatiques
- Loss Recovery System
- Correlation Detector (évite surexposition)
- Flash Crash Protection
- Liquidation Guard
- Auto-rebalancing
"""

import logging
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, timedelta
import numpy as np

LOG = logging.getLogger("smart_position_manager")
LOG.setLevel(logging.INFO)

class PositionAction(Enum):
    """Actions possibles sur une position"""
    HOLD = "hold"
    SELL_PARTIAL = "sell_partial"
    CLOSE_PARTIAL = "close_partial"
    CLOSE_NOW = "close_now"
    TRAILING_STOP = "trailing_stop"
    MOVE_TO_BREAKEVEN = "move_to_breakeven"
    RECOVERY_MODE = "recovery_mode"

class SmartPositionManager:
    """
    Gestionnaire intelligent de positions
    
    Features:
    - Auto-décisions selon PnL, temps, liquidation risk
    - Loss Recovery System (récupère pertes intelligemment)
    - Correlation Detector (évite BTC+ETH simultanément)
    - Flash Crash Protection
    """
    
    def __init__(self):
        """Initialize Smart Position Manager"""
        self.positions: Dict[str, Dict] = {}
        self.closed_positions: List[Dict] = []
        
        # Loss Recovery System
        self.recovery_mode = False
        self.total_losses = 0.0
        self.recovery_target = 0.0
        self.recovery_strategy = "conservative"  # conservative, moderate, aggressive
        
        # Correlation tracking
        self.correlation_matrix = {}
        self.max_correlation_exposure = 0.7  # Max 70% en coins corrélés
        
        # Flash Crash Protection
        self.flash_crash_active = False
        self.price_history = {}  # coin -> list of prices
        
        # Stats
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        
        LOG.info("✅ Smart Position Manager initialized")
    
    def add_position(self, coin: str, position: Dict) -> bool:
        """
        Ajoute une nouvelle position
        
        Args:
            coin: Symbol du coin
            position: Dict avec entry_price, amount, type, etc.
        
        Returns:
            True si ajouté
        """
        # Check correlation avant d'ajouter
        if not self._check_correlation_safety(coin):
            LOG.warning(f"⚠️ Position {coin} rejected - correlation risk too high")
            return False
        
        position['opened_at'] = datetime.now().isoformat()
        position['status'] = 'OPEN'
        self.positions[coin] = position
        
        LOG.info(f"✅ Position added: {coin} @ ${position['entry_price']:.2f}")
        return True
    
    def _check_correlation_safety(self, new_coin: str) -> bool:
        """
        Vérifie si ajouter cette position ne crée pas de surexposition corrélée
        
        Args:
            new_coin: Nouveau coin à ajouter
        
        Returns:
            True si safe
        """
        # Coins hautement corrélés (simplifié)
        correlations = {
            'BTC': ['ETH', 'LTC', 'BCH'],
            'ETH': ['BTC', 'BNB', 'LINK'],
            'BNB': ['ETH', 'CAKE'],
            'SOL': ['AVAX', 'FTM'],
            'MATIC': ['AVAX', 'FTM']
        }
        
        new_coin_base = new_coin.split('/')[0] if '/' in new_coin else new_coin
        
        # Check combien de positions corrélées on a déjà
        correlated_count = 0
        total_positions = len(self.positions)
        
        for existing_coin in self.positions.keys():
            existing_base = existing_coin.split('/')[0] if '/' in existing_coin else existing_coin
            
            # Check si corrélé
            if existing_base in correlations.get(new_coin_base, []):
                correlated_count += 1
        
        if total_positions > 0:
            correlation_ratio = correlated_count / total_positions
            
            if correlation_ratio > self.max_correlation_exposure:
                LOG.warning(f"⚠️ Correlation too high: {correlation_ratio:.1%} (max: {self.max_correlation_exposure:.1%})")
                return False
        
        return True
    
    def update_price_history(self, coin: str, price: float):
        """
        Met à jour l'historique des prix pour flash crash detection
        
        Args:
            coin: Symbol
            price: Prix actuel
        """
        if coin not in self.price_history:
            self.price_history[coin] = []
        
        self.price_history[coin].append({
            'price': price,
            'timestamp': datetime.now()
        })
        
        # Garde seulement dernières 5 minutes
        cutoff = datetime.now() - timedelta(minutes=5)
        self.price_history[coin] = [
            p for p in self.price_history[coin] 
            if datetime.fromisoformat(p['timestamp'].isoformat()) > cutoff
        ]
    
    def detect_flash_crash(self, coin: str) -> bool:
        """
        Détecte flash crash (chute > 10% en < 5min)
        
        Args:
            coin: Symbol
        
        Returns:
            True si flash crash détecté
        """
        if coin not in self.price_history or len(self.price_history[coin]) < 2:
            return False
        
        # Prix il y a 5min vs maintenant
        oldest_price = self.price_history[coin][0]['price']
        current_price = self.price_history[coin][-1]['price']
        
        drop_percent = ((current_price - oldest_price) / oldest_price) * 100
        
        if drop_percent < -10.0:
            LOG.error(f"🚨 FLASH CRASH DETECTED on {coin}: {drop_percent:.2f}%")
            self.flash_crash_active = True
            return True
        
        return False
    
    def analyze_position(self, coin: str, current_price: float, market_data: Dict) -> Dict:
        """
        Analyse une position et recommande une action
        
        Args:
            coin: Symbol
            current_price: Prix actuel
            market_data: Données de marché
        
        Returns:
            Dict avec action recommandée et raison
        """
        if coin not in self.positions:
            return {'action': PositionAction.HOLD, 'reason': 'No position'}
        
        position = self.positions[coin]
        entry_price = position['entry_price']
        pos_type = position.get('type', 'SPOT')
        
        # Calculate PnL
        if pos_type == 'SPOT':
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
        else:  # FUTURES
            side = position.get('side', 'LONG')
            if side == 'LONG':
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_percent = ((entry_price - current_price) / entry_price) * 100
        
        # Temps depuis ouverture
        opened_at = datetime.fromisoformat(position['opened_at'])
        time_open_hours = (datetime.now() - opened_at).total_seconds() / 3600
        
        # ==================
        # DÉCISIONS SPOT
        # ==================
        if pos_type == 'SPOT':
            # 🚨 Flash crash - CLOSE immédiatement
            if self.detect_flash_crash(coin):
                return {
                    'action': PositionAction.CLOSE_NOW,
                    'reason': 'Flash crash detected - emergency close',
                    'urgency': 'CRITICAL'
                }
            
            # ✅ Gros profit > 10% - Vendre 50% + trailing
            if pnl_percent > 10.0:
                return {
                    'action': PositionAction.SELL_PARTIAL,
                    'percent': 50,
                    'reason': f'Big profit {pnl_percent:.2f}% - secure 50% + trailing',
                    'urgency': 'HIGH'
                }
            
            # 💰 Profit modéré > 5% - Hold + trailing
            elif pnl_percent > 5.0:
                return {
                    'action': PositionAction.TRAILING_STOP,
                    'offset': 2.0,
                    'reason': f'Profit {pnl_percent:.2f}% - activate trailing',
                    'urgency': 'MEDIUM'
                }
            
            # ❌ Loss > 5% - SELL (stop loss)
            elif pnl_percent < -5.0:
                # Active Recovery Mode
                if not self.recovery_mode:
                    self._activate_recovery_mode(abs(pnl_percent * position['amount'] * entry_price / 100))
                
                return {
                    'action': PositionAction.CLOSE_NOW,
                    'reason': f'Stop loss hit: {pnl_percent:.2f}%',
                    'urgency': 'HIGH'
                }
            
            # ⏰ Position ouverte > 7 jours - Review
            elif time_open_hours > 168:  # 7 jours
                if pnl_percent < 0:
                    return {
                        'action': PositionAction.CLOSE_NOW,
                        'reason': 'Position open too long with loss',
                        'urgency': 'MEDIUM'
                    }
                else:
                    return {
                        'action': PositionAction.HOLD,
                        'reason': 'Position profitable, hold',
                        'urgency': 'LOW'
                    }
        
        # ==================
        # DÉCISIONS FUTURES
        # ==================
        else:
            leverage = position.get('leverage', 1)
            liquidation_price = position.get('liquidation_price', 0)
            
            # 🚨 Liquidation risk < 5% - CLOSE IMMÉDIATEMENT
            if liquidation_price > 0:
                distance_to_liq = abs((current_price - liquidation_price) / liquidation_price) * 100
                
                if distance_to_liq < 5.0:
                    return {
                        'action': PositionAction.CLOSE_NOW,
                        'reason': f'LIQUIDATION RISK: {distance_to_liq:.2f}% to liquidation!',
                        'urgency': 'CRITICAL'
                    }
            
            # ✅ Profit > 10% - Close 50%
            if pnl_percent > 10.0:
                return {
                    'action': PositionAction.CLOSE_PARTIAL,
                    'percent': 50,
                    'reason': f'Big profit {pnl_percent:.2f}% - secure 50%',
                    'urgency': 'HIGH'
                }
            
            # ❌ Loss > 5% - Stop loss
            elif pnl_percent < -5.0:
                if not self.recovery_mode:
                    self._activate_recovery_mode(abs(pnl_percent * position['amount'] * entry_price / 100))
                
                return {
                    'action': PositionAction.CLOSE_NOW,
                    'reason': f'Stop loss: {pnl_percent:.2f}%',
                    'urgency': 'HIGH'
                }
            
            # 💸 Funding rate < -0.1% - Alerte
            funding_rate = market_data.get('funding_rate', 0)
            if funding_rate < -0.1:
                return {
                    'action': PositionAction.HOLD,
                    'reason': f'Negative funding {funding_rate:.3f}% - monitor',
                    'urgency': 'MEDIUM'
                }
        
        # Default: HOLD
        return {
            'action': PositionAction.HOLD,
            'reason': f'Position normal (PnL: {pnl_percent:+.2f}%)',
            'urgency': 'LOW'
        }
    
    def _activate_recovery_mode(self, loss_amount: float):
        """
        Active le Loss Recovery System
        
        Args:
            loss_amount: Montant de la perte
        """
        self.recovery_mode = True
        self.total_losses += loss_amount
        self.recovery_target = self.total_losses * 1.1  # Récupère +10%
        
        LOG.warning(f"🔴 RECOVERY MODE ACTIVATED - Loss: ${loss_amount:.2f} | Target: ${self.recovery_target:.2f}")
    
    def get_recovery_strategy(self) -> Dict:
        """
        Retourne la stratégie de récupération des pertes
        
        Returns:
            Dict avec stratégie adaptée
        """
        if not self.recovery_mode:
            return {'active': False}
        
        # Stratégie selon montant de perte
        if self.total_losses < 100:
            strategy = "conservative"
            recommendations = {
                'risk_level': 'LOW',
                'position_size': '5%',
                'strategies': ['DCA Strategy', 'Grid Trading'],
                'leverage': 1,
                'description': 'Récupération douce avec stratégies sûres'
            }
        elif self.total_losses < 500:
            strategy = "moderate"
            recommendations = {
                'risk_level': 'MEDIUM',
                'position_size': '8%',
                'strategies': ['Scalping', 'Trend Following'],
                'leverage': 2,
                'description': 'Récupération modérée avec scalping'
            }
        else:
            strategy = "aggressive"
            recommendations = {
                'risk_level': 'HIGH',
                'position_size': '3%',
                'strategies': ['Adaptive Scalping', 'Flash Crash Hunter'],
                'leverage': 1,
                'description': 'Récupération prudente malgré perte importante'
            }
        
        return {
            'active': True,
            'total_losses': self.total_losses,
            'recovery_target': self.recovery_target,
            'progress_percent': (self.recovery_target - self.total_losses) / self.recovery_target * 100,
            'strategy': strategy,
            'recommendations': recommendations
        }
    
    def execute_action(self, coin: str, action_data: Dict) -> bool:
        """
        Execute l'action recommandée
        
        Args:
            coin: Symbol
            action_data: Action à executer
        
        Returns:
            True si succès
        """
        if coin not in self.positions:
            return False
        
        action = action_data['action']
        position = self.positions[coin]
        
        if action == PositionAction.CLOSE_NOW:
            # Ferme position complètement
            self.closed_positions.append(position)
            del self.positions[coin]
            LOG.info(f"✅ Position {coin} closed: {action_data['reason']}")
            return True
        
        elif action == PositionAction.SELL_PARTIAL:
            # Vend une partie
            percent = action_data.get('percent', 50)
            position['amount'] *= (1 - percent / 100)
            LOG.info(f"✅ Position {coin} reduced {percent}%")
            return True
        
        elif action == PositionAction.TRAILING_STOP:
            # Active trailing stop
            position['trailing_enabled'] = True
            position['trailing_offset'] = action_data.get('offset', 2.0)
            LOG.info(f"✅ Trailing stop activated for {coin}")
            return True
        
        # Autres actions...
        return True
    
    def get_correlation_report(self) -> Dict:
        """Retourne rapport de corrélation des positions"""
        coins = list(self.positions.keys())
        
        if len(coins) < 2:
            return {'correlation_risk': 'LOW', 'diversification': 100}
        
        # Simplifié: compte combien de coins corrélés
        correlated_pairs = 0
        total_pairs = 0
        
        for i, coin1 in enumerate(coins):
            for coin2 in coins[i+1:]:
                total_pairs += 1
                if self._are_correlated(coin1, coin2):
                    correlated_pairs += 1
        
        correlation_percent = (correlated_pairs / total_pairs * 100) if total_pairs > 0 else 0
        
        if correlation_percent > 70:
            risk = 'HIGH'
        elif correlation_percent > 40:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'
        
        return {
            'correlation_risk': risk,
            'correlation_percent': correlation_percent,
            'diversification': 100 - correlation_percent,
            'recommendation': 'Reduce correlated positions' if risk == 'HIGH' else 'Good diversification'
        }
    
    def _are_correlated(self, coin1: str, coin2: str) -> bool:
        """Check si 2 coins sont corrélés"""
        correlations = {
            'BTC': ['ETH', 'LTC', 'BCH'],
            'ETH': ['BTC', 'BNB', 'LINK'],
            'BNB': ['ETH', 'CAKE'],
        }
        
        base1 = coin1.split('/')[0] if '/' in coin1 else coin1
        base2 = coin2.split('/')[0] if '/' in coin2 else coin2
        
        return base2 in correlations.get(base1, []) or base1 in correlations.get(base2, [])
    
    def get_stats(self) -> Dict:
        """Statistiques du manager"""
        total_trades = self.win_count + self.loss_count
        win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'open_positions': len(self.positions),
            'closed_positions': len(self.closed_positions),
            'total_pnl': self.total_pnl,
            'win_rate': win_rate,
            'recovery_mode': self.recovery_mode,
            'flash_crash_active': self.flash_crash_active,
            'correlation_report': self.get_correlation_report()
        }


# Singleton
_manager = None

def get_position_manager() -> SmartPositionManager:
    """Retourne instance singleton"""
    global _manager
    if _manager is None:
        _manager = SmartPositionManager()
    return _manager
