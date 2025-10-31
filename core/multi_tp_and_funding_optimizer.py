#!/usr/bin/env python3
"""
💰 MULTI-TP & FUNDING RATE OPTIMIZER
====================================
by MAIGA ABOUBACAR

Features:
- Take Profit multi-niveaux (TP1/TP2/TP3)
- Funding Rate Optimizer (profite des funding positifs)
- Trailing automatique après TP1
- Breakeven move après TP2
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

LOG = logging.getLogger("multi_tp_funding")
LOG.setLevel(logging.INFO)

@dataclass
class TPLevel:
    """Un niveau de Take Profit"""
    percent: float           # % de profit
    close_percent: float     # % de position à fermer
    executed: bool = False
    price: float = 0.0

class MultiTPHandler:
    """
    Gestionnaire de Take Profit multi-niveaux
    
    Exemple:
    - TP1: +2% → Close 30%
    - TP2: +4% → Close 40%
    - TP3: +8% → Close 30% restant
    """
    
    def __init__(self):
        """Initialize Multi-TP Handler"""
        self.positions = {}
        LOG.info("✅ Multi-TP Handler initialized")
    
    def create_multi_tp(self, coin: str, entry_price: float, 
                       side: str, initial_amount: float,
                       tp_levels: List[Dict]) -> Dict:
        """
        Crée une position avec multi-TP
        
        Args:
            coin: Symbol
            entry_price: Prix d'entrée
            side: LONG ou SHORT
            initial_amount: Quantité initiale
            tp_levels: Liste des niveaux TP [{percent, close_percent}, ...]
        
        Returns:
            Position dict
        """
        # Convert dict to TPLevel objects
        levels = []
        for tp in tp_levels:
            if side == 'LONG':
                price = entry_price * (1 + tp['percent'] / 100)
            else:
                price = entry_price * (1 - tp['percent'] / 100)
            
            levels.append(TPLevel(
                percent=tp['percent'],
                close_percent=tp['close_percent'],
                price=price
            ))
        
        position = {
            'coin': coin,
            'entry_price': entry_price,
            'side': side,
            'initial_amount': initial_amount,
            'remaining_amount': initial_amount,
            'tp_levels': levels,
            'trailing_enabled': False,
            'breakeven_moved': False,
            'total_closed': 0.0,
            'total_pnl': 0.0,
            'opened_at': datetime.now().isoformat()
        }
        
        self.positions[coin] = position
        
        LOG.info(f"✅ Multi-TP position created: {coin} {side} @ ${entry_price:.2f}")
        for i, level in enumerate(levels, 1):
            LOG.info(f"   TP{i}: ${level.price:.2f} ({level.percent}%) → Close {level.close_percent}%")
        
        return position
    
    def check_tp_levels(self, coin: str, current_price: float) -> List[Dict]:
        """
        Vérifie si des niveaux TP sont atteints
        
        Args:
            coin: Symbol
            current_price: Prix actuel
        
        Returns:
            Liste des actions à executer
        """
        if coin not in self.positions:
            return []
        
        position = self.positions[coin]
        actions = []
        
        for i, tp_level in enumerate(position['tp_levels'], 1):
            if tp_level.executed:
                continue
            
            tp_hit = False
            
            if position['side'] == 'LONG':
                tp_hit = current_price >= tp_level.price
            else:
                tp_hit = current_price <= tp_level.price
            
            if tp_hit:
                # Calculate amount to close
                amount_to_close = position['remaining_amount'] * (tp_level.close_percent / 100)
                
                # Calculate PnL for this TP
                if position['side'] == 'LONG':
                    pnl = (current_price - position['entry_price']) * amount_to_close
                else:
                    pnl = (position['entry_price'] - current_price) * amount_to_close
                
                tp_level.executed = True
                position['remaining_amount'] -= amount_to_close
                position['total_closed'] += amount_to_close
                position['total_pnl'] += pnl
                
                actions.append({
                    'type': 'TP_HIT',
                    'level': i,
                    'price': current_price,
                    'amount_closed': amount_to_close,
                    'remaining': position['remaining_amount'],
                    'pnl': pnl
                })
                
                LOG.info(f"✅ TP{i} HIT for {coin}: Closed {amount_to_close:.6f} @ ${current_price:.2f} | PnL: ${pnl:+.2f}")
                
                # Active trailing après TP1
                if i == 1 and not position['trailing_enabled']:
                    position['trailing_enabled'] = True
                    actions.append({
                        'type': 'TRAILING_ACTIVATED',
                        'offset': 2.0
                    })
                    LOG.info(f"🔄 Trailing stop activated for {coin}")
                
                # Move SL to breakeven après TP2
                if i == 2 and not position['breakeven_moved']:
                    position['breakeven_moved'] = True
                    actions.append({
                        'type': 'BREAKEVEN_MOVE',
                        'sl_price': position['entry_price']
                    })
                    LOG.info(f"🛡️ Stop Loss moved to breakeven for {coin}")
        
        return actions
    
    def get_position_status(self, coin: str) -> Optional[Dict]:
        """Retourne le statut d'une position"""
        if coin not in self.positions:
            return None
        
        position = self.positions[coin]
        
        executed_tps = sum(1 for tp in position['tp_levels'] if tp.executed)
        total_tps = len(position['tp_levels'])
        
        return {
            'coin': coin,
            'entry_price': position['entry_price'],
            'side': position['side'],
            'remaining_amount': position['remaining_amount'],
            'closed_percent': (position['total_closed'] / position['initial_amount']) * 100,
            'tps_executed': f"{executed_tps}/{total_tps}",
            'total_pnl': position['total_pnl'],
            'trailing_enabled': position['trailing_enabled'],
            'breakeven_moved': position['breakeven_moved']
        }


class FundingRateOptimizer:
    """
    Optimiseur de Funding Rate pour Futures
    
    Profite des funding rates positifs en:
    - Ouvrant positions quand funding favorable
    - Fermant positions avant funding défavorable
    - Arbitrage funding rate (long sur exchange A, short sur B)
    """
    
    def __init__(self):
        """Initialize Funding Rate Optimizer"""
        self.funding_history = {}
        self.optimal_threshold = 0.01  # 0.01% = opportunité
        LOG.info("✅ Funding Rate Optimizer initialized")
    
    def analyze_funding_rate(self, coin: str, current_funding: float,
                            predicted_funding: Optional[float] = None) -> Dict:
        """
        Analyse le funding rate et recommande action
        
        Args:
            coin: Symbol
            current_funding: Funding rate actuel (en %)
            predicted_funding: Funding rate prédit prochain
        
        Returns:
            Dict avec recommandation
        """
        # Store history
        if coin not in self.funding_history:
            self.funding_history[coin] = []
        
        self.funding_history[coin].append({
            'rate': current_funding,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 24 funding rates (24h with 1h funding)
        self.funding_history[coin] = self.funding_history[coin][-24:]
        
        # Calculate average
        if len(self.funding_history[coin]) > 0:
            avg_funding = sum(f['rate'] for f in self.funding_history[coin]) / len(self.funding_history[coin])
        else:
            avg_funding = current_funding
        
        recommendation = {
            'coin': coin,
            'current_funding': current_funding,
            'avg_funding_24h': avg_funding,
            'action': 'NEUTRAL',
            'reason': '',
            'opportunity_score': 0
        }
        
        # 💰 Funding TRÈS positif (> 0.05%) - Opportunité SHORT
        if current_funding > 0.05:
            recommendation.update({
                'action': 'SHORT',
                'reason': f'High positive funding {current_funding:.4f}% - profit from shorts',
                'opportunity_score': min(100, current_funding * 1000)  # Score 0-100
            })
        
        # 💰 Funding positif modéré (> 0.01%) - Favorable SHORT
        elif current_funding > self.optimal_threshold:
            recommendation.update({
                'action': 'SHORT_FAVORABLE',
                'reason': f'Positive funding {current_funding:.4f}% - shorts earn funding',
                'opportunity_score': min(70, current_funding * 700)
            })
        
        # 📉 Funding négatif modéré (< -0.01%) - Favorable LONG
        elif current_funding < -self.optimal_threshold:
            recommendation.update({
                'action': 'LONG_FAVORABLE',
                'reason': f'Negative funding {current_funding:.4f}% - longs earn funding',
                'opportunity_score': min(70, abs(current_funding) * 700)
            })
        
        # 📉 Funding TRÈS négatif (< -0.05%) - Opportunité LONG
        elif current_funding < -0.05:
            recommendation.update({
                'action': 'LONG',
                'reason': f'High negative funding {current_funding:.4f}% - profit from longs',
                'opportunity_score': min(100, abs(current_funding) * 1000)
            })
        
        # 🔄 Funding proche de 0 - Neutre
        else:
            recommendation.update({
                'action': 'NEUTRAL',
                'reason': f'Neutral funding {current_funding:.4f}%',
                'opportunity_score': 0
            })
        
        # Check predicted funding si disponible
        if predicted_funding is not None:
            if abs(predicted_funding - current_funding) > 0.02:
                recommendation['warning'] = f'Big funding change expected: {current_funding:.4f}% → {predicted_funding:.4f}%'
        
        return recommendation
    
    def should_close_before_funding(self, coin: str, position_side: str,
                                   current_funding: float, time_to_funding_minutes: int) -> bool:
        """
        Détermine si on doit fermer position avant le funding
        
        Args:
            coin: Symbol
            position_side: LONG ou SHORT
            current_funding: Funding rate actuel
            time_to_funding_minutes: Minutes avant prochain funding
        
        Returns:
            True si doit fermer
        """
        # Si funding dans < 10 minutes et défavorable
        if time_to_funding_minutes < 10:
            # LONG position + funding très positif = on paye
            if position_side == 'LONG' and current_funding > 0.05:
                LOG.warning(f"⚠️ {coin}: Close LONG before paying {current_funding:.4f}% funding!")
                return True
            
            # SHORT position + funding très négatif = on paye
            elif position_side == 'SHORT' and current_funding < -0.05:
                LOG.warning(f"⚠️ {coin}: Close SHORT before paying {abs(current_funding):.4f}% funding!")
                return True
        
        return False
    
    def get_funding_arbitrage_opportunity(self, coin: str, 
                                         exchange_a_funding: float,
                                         exchange_b_funding: float) -> Optional[Dict]:
        """
        Détecte opportunité d'arbitrage funding rate entre exchanges
        
        Args:
            coin: Symbol
            exchange_a_funding: Funding rate exchange A
            exchange_b_funding: Funding rate exchange B
        
        Returns:
            Opportunité d'arbitrage si présente
        """
        spread = abs(exchange_a_funding - exchange_b_funding)
        
        # Opportunité si spread > 0.03% (0.0003)
        if spread > 0.03:
            # Determine which side on which exchange
            if exchange_a_funding > exchange_b_funding:
                # Exchange A funding plus élevé
                return {
                    'opportunity': True,
                    'type': 'FUNDING_ARBITRAGE',
                    'exchange_a_action': 'SHORT',  # Receive funding
                    'exchange_b_action': 'LONG',   # Pay less funding
                    'spread': spread,
                    'potential_profit_percent': spread,
                    'reason': f'Funding spread {spread:.4f}%'
                }
            else:
                return {
                    'opportunity': True,
                    'type': 'FUNDING_ARBITRAGE',
                    'exchange_a_action': 'LONG',
                    'exchange_b_action': 'SHORT',
                    'spread': spread,
                    'potential_profit_percent': spread,
                    'reason': f'Funding spread {spread:.4f}%'
                }
        
        return None


# Singletons
_multi_tp = None
_funding_optimizer = None

def get_multi_tp_handler() -> MultiTPHandler:
    """Retourne instance Multi-TP Handler"""
    global _multi_tp
    if _multi_tp is None:
        _multi_tp = MultiTPHandler()
    return _multi_tp

def get_funding_optimizer() -> FundingRateOptimizer:
    """Retourne instance Funding Rate Optimizer"""
    global _funding_optimizer
    if _funding_optimizer is None:
        _funding_optimizer = FundingRateOptimizer()
    return _funding_optimizer
