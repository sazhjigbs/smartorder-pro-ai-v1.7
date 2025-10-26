"""
SmartOrder PRO - Smart Compounding Engine
Réinvestit automatiquement les profits de manière optimale
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque

LOG = logging.getLogger("smart_compounding")
LOG.setLevel(logging.INFO)

class SmartCompounding:
    """
    Gère le compounding intelligent des profits
    
    Stratégies:
    1. Fixed Percentage: Réinvestir X% des profits
    2. Kelly Criterion: Taille optimale selon win rate et odds
    3. Volatility-Adjusted: Réduire réinvestissement en haute volatilité
    4. Profit Target: Accumuler jusqu'à un seuil puis réinvestir
    5. Risk-Based: Ajuster selon drawdown actuel
    
    Objectif: Maximiser la croissance tout en contrôlant le risque
    
    Avec compounding 50% sur 10 trades gagnants de +10%:
    Sans compounding: +100% (10 trades × 10%)
    Avec compounding: +163% (croissance exponentielle)
    """
    
    def __init__(self, initial_capital: float = 1000.0):
        """
        Initialize Smart Compounding
        
        Args:
            initial_capital: Capital initial en USDT
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.total_profit = 0.0
        self.total_loss = 0.0
        
        # Historique des trades
        self.trade_history = deque(maxlen=100)
        
        # Paramètres de compounding
        self.compound_pct = 50.0  # Réinvestir 50% des profits par défaut
        self.min_profit_threshold = 10.0  # Minimum $10 de profit pour compounding
        self.max_position_pct = 20.0  # Maximum 20% du capital par position
        
        # Paramètres Kelly
        self.kelly_fraction = 0.25  # Utiliser 25% du Kelly (Kelly fractionnel)
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_compounded': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0,
            'peak_capital': initial_capital
        }
        
        LOG.info(f"SmartCompounding initialized with ${initial_capital:.2f}")
    
    def record_trade(self, trade_result: Dict):
        """
        Enregistre le résultat d'un trade
        
        Args:
            trade_result: {
                'symbol': str,
                'side': 'BUY' | 'SELL',
                'entry_price': float,
                'exit_price': float,
                'quantity': float,
                'profit_usdt': float,
                'profit_pct': float,
                'timestamp': str
            }
        """
        profit = trade_result.get('profit_usdt', 0.0)
        
        # Ajouter à l'historique
        self.trade_history.append({
            **trade_result,
            'capital_before': self.current_capital,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mettre à jour stats
        self.stats['total_trades'] += 1
        
        if profit > 0:
            self.stats['winning_trades'] += 1
            self.total_profit += profit
        else:
            self.stats['losing_trades'] += 1
            self.total_loss += abs(profit)
        
        # Mettre à jour capital
        self.current_capital += profit
        
        # Track peak et drawdown
        if self.current_capital > self.stats['peak_capital']:
            self.stats['peak_capital'] = self.current_capital
        
        drawdown = ((self.stats['peak_capital'] - self.current_capital) / 
                   self.stats['peak_capital'] * 100)
        
        if drawdown > self.stats['max_drawdown']:
            self.stats['max_drawdown'] = drawdown
        
        # Calculer avg win/loss
        if self.stats['winning_trades'] > 0:
            self.stats['avg_win'] = self.total_profit / self.stats['winning_trades']
        
        if self.stats['losing_trades'] > 0:
            self.stats['avg_loss'] = self.total_loss / self.stats['losing_trades']
        
        LOG.info(f"Trade recorded: {trade_result['symbol']} "
                f"P&L: ${profit:.2f} | Capital: ${self.current_capital:.2f}")
    
    def calculate_kelly_size(self) -> float:
        """
        Calcule la taille de position optimale selon Kelly Criterion
        
        Kelly% = (W * (R+1) - 1) / R
        où:
        - W = win rate
        - R = avg_win / avg_loss (reward/risk ratio)
        
        Returns:
            Pourcentage du capital à risquer (0-100)
        """
        total_trades = self.stats['total_trades']
        
        if total_trades < 10:
            # Pas assez de données, utiliser conservateur
            return 10.0
        
        win_rate = self.stats['winning_trades'] / total_trades
        
        avg_win = self.stats.get('avg_win', 0)
        avg_loss = self.stats.get('avg_loss', 1)  # Éviter division par zéro
        
        if avg_loss == 0:
            avg_loss = 1
        
        reward_risk_ratio = avg_win / avg_loss
        
        # Kelly formula
        kelly_pct = ((win_rate * (reward_risk_ratio + 1) - 1) / reward_risk_ratio) * 100
        
        # Kelly fractionnel pour réduire variance
        fractional_kelly = kelly_pct * self.kelly_fraction
        
        # Limiter entre 5% et 30%
        kelly_size = max(5.0, min(30.0, fractional_kelly))
        
        LOG.debug(f"Kelly calculation: WR={win_rate:.2%}, R:R={reward_risk_ratio:.2f}, "
                 f"Kelly={kelly_pct:.1f}%, Fractional={kelly_size:.1f}%")
        
        return kelly_size
    
    def calculate_compound_amount(self, recent_profit: float, 
                                  strategy: str = "fixed", 
                                  volatility_score: float = 50.0) -> float:
        """
        Calcule le montant à compounding
        
        Args:
            recent_profit: Profit récent en USDT
            strategy: 'fixed' | 'kelly' | 'volatility_adjusted' | 'profit_target'
            volatility_score: Score de volatilité 0-100
            
        Returns:
            Montant à réinvestir en USDT
        """
        # Vérifier seuil minimum
        if recent_profit < self.min_profit_threshold:
            LOG.debug(f"Profit ${recent_profit:.2f} below threshold ${self.min_profit_threshold:.2f}")
            return 0.0
        
        if strategy == "fixed":
            # Stratégie fixe: réinvestir X% du profit
            compound_amount = recent_profit * (self.compound_pct / 100)
        
        elif strategy == "kelly":
            # Utiliser Kelly Criterion
            kelly_pct = self.calculate_kelly_size()
            compound_amount = self.current_capital * (kelly_pct / 100)
        
        elif strategy == "volatility_adjusted":
            # Réduire compounding en haute volatilité
            # Vol 0-30: 100% du compound_pct
            # Vol 30-60: 75%
            # Vol 60-80: 50%
            # Vol 80-100: 25%
            
            if volatility_score < 30:
                vol_multiplier = 1.0
            elif volatility_score < 60:
                vol_multiplier = 0.75
            elif volatility_score < 80:
                vol_multiplier = 0.5
            else:
                vol_multiplier = 0.25
            
            compound_amount = recent_profit * (self.compound_pct / 100) * vol_multiplier
        
        elif strategy == "profit_target":
            # Accumuler jusqu'à un seuil (ex: $100) puis réinvestir tout
            unreinvested_profit = self.current_capital - self.initial_capital
            
            profit_target = 100.0  # $100
            
            if unreinvested_profit >= profit_target:
                compound_amount = unreinvested_profit
            else:
                compound_amount = 0.0
        
        else:
            # Par défaut: fixed
            compound_amount = recent_profit * (self.compound_pct / 100)
        
        # Limiter à un max (ex: 20% du capital actuel)
        max_compound = self.current_capital * (self.max_position_pct / 100)
        compound_amount = min(compound_amount, max_compound)
        
        self.stats['total_compounded'] += compound_amount
        
        LOG.info(f"Compound calculation: Profit=${recent_profit:.2f}, "
                f"Strategy={strategy}, Amount=${compound_amount:.2f}")
        
        return compound_amount
    
    def get_next_position_size(self, symbol: str, 
                               entry_price: float,
                               strategy: str = "kelly",
                               volatility_score: float = 50.0) -> Dict:
        """
        Calcule la taille de position optimale pour le prochain trade
        
        Args:
            symbol: Symbole à trader
            entry_price: Prix d'entrée prévu
            strategy: Stratégie de sizing
            volatility_score: Score de volatilité
            
        Returns:
            {
                'position_size_usdt': float,
                'position_size_pct': float,
                'quantity': float,
                'reasoning': str
            }
        """
        # Calculer la taille selon stratégie
        if strategy == "kelly":
            size_pct = self.calculate_kelly_size()
        elif strategy == "fixed":
            size_pct = 10.0  # 10% fixe
        elif strategy == "volatility_adjusted":
            # Réduire en haute vol
            base_pct = 10.0
            if volatility_score < 40:
                size_pct = base_pct * 1.2
            elif volatility_score < 60:
                size_pct = base_pct
            else:
                size_pct = base_pct * 0.6
        else:
            size_pct = 10.0
        
        # Ajuster selon drawdown actuel
        drawdown = self.stats.get('max_drawdown', 0)
        
        if drawdown > 20:
            # Drawdown > 20%, réduire position
            size_pct *= 0.5
            reasoning = f"Reduced due to {drawdown:.1f}% drawdown"
        elif drawdown > 10:
            size_pct *= 0.75
            reasoning = f"Slightly reduced due to {drawdown:.1f}% drawdown"
        else:
            reasoning = "Normal sizing"
        
        # Limiter à max_position_pct
        size_pct = min(size_pct, self.max_position_pct)
        
        # Calculer montant en USDT
        position_size_usdt = self.current_capital * (size_pct / 100)
        
        # Calculer quantité
        quantity = position_size_usdt / entry_price if entry_price > 0 else 0
        
        result = {
            'symbol': symbol,
            'position_size_usdt': round(position_size_usdt, 2),
            'position_size_pct': round(size_pct, 2),
            'quantity': round(quantity, 6),
            'entry_price': entry_price,
            'strategy': strategy,
            'reasoning': reasoning
        }
        
        LOG.info(f"Position sizing for {symbol}: ${position_size_usdt:.2f} "
                f"({size_pct:.1f}%) = {quantity:.6f} units")
        
        return result
    
    def get_roi(self) -> Dict:
        """
        Calcule le ROI et les métriques de performance
        
        Returns:
            {
                'initial_capital': float,
                'current_capital': float,
                'total_profit': float,
                'roi_pct': float,
                'roi_with_compounding': float,
                'roi_without_compounding': float,
                'compound_benefit': float
            }
        """
        roi_pct = ((self.current_capital - self.initial_capital) / 
                  self.initial_capital * 100)
        
        # Calculer ROI sans compounding (additif)
        if self.stats['total_trades'] > 0:
            # Supposer même win rate mais capital fixe
            avg_profit_per_trade = (self.total_profit - self.total_loss) / self.stats['total_trades']
            total_profit_no_compound = avg_profit_per_trade * self.stats['total_trades']
            roi_no_compound = (total_profit_no_compound / self.initial_capital) * 100
        else:
            roi_no_compound = 0.0
        
        compound_benefit = roi_pct - roi_no_compound
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': round(self.current_capital, 2),
            'total_profit': round(self.total_profit, 2),
            'total_loss': round(self.total_loss, 2),
            'net_profit': round(self.total_profit - self.total_loss, 2),
            'roi_pct': round(roi_pct, 2),
            'roi_with_compounding': round(roi_pct, 2),
            'roi_without_compounding': round(roi_no_compound, 2),
            'compound_benefit': round(compound_benefit, 2)
        }
    
    def get_stats(self) -> Dict:
        """Retourne toutes les statistiques"""
        roi = self.get_roi()
        
        win_rate = 0.0
        if self.stats['total_trades'] > 0:
            win_rate = (self.stats['winning_trades'] / self.stats['total_trades']) * 100
        
        return {
            **self.stats,
            'win_rate': round(win_rate, 1),
            **roi
        }
    
    def reset(self):
        """Réinitialise le capital et les stats (pour backtesting)"""
        self.current_capital = self.initial_capital
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.trade_history.clear()
        
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_compounded': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0,
            'peak_capital': self.initial_capital
        }
        
        LOG.info("SmartCompounding reset")


# Instance globale
_smart_compounding = None

def get_smart_compounding(initial_capital: float = 1000.0) -> SmartCompounding:
    """Récupère l'instance singleton"""
    global _smart_compounding
    if _smart_compounding is None:
        _smart_compounding = SmartCompounding(initial_capital)
    return _smart_compounding


if __name__ == "__main__":
    # Test du module
    print("=" * 60)
    print("Smart Compounding Engine - Test")
    print("=" * 60)
    
    compounder = SmartCompounding(initial_capital=1000.0)
    
    print(f"\n💰 Capital initial: ${compounder.initial_capital:.2f}")
    
    # Simuler 10 trades gagnants
    print(f"\n📊 Simulation de 10 trades...")
    
    for i in range(10):
        # Trade gagnant de +10%
        entry_price = 100.0
        exit_price = 110.0
        
        # Position sizing
        position = compounder.get_next_position_size(
            "BTCUSDT", 
            entry_price,
            strategy="kelly"
        )
        
        quantity = position['quantity']
        profit_usdt = (exit_price - entry_price) * quantity
        profit_pct = 10.0
        
        trade_result = {
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'profit_usdt': profit_usdt,
            'profit_pct': profit_pct,
            'timestamp': datetime.now().isoformat()
        }
        
        compounder.record_trade(trade_result)
        
        print(f"   Trade {i+1}: +${profit_usdt:.2f} | "
              f"Capital: ${compounder.current_capital:.2f}")
    
    # Stats finales
    print(f"\n📊 Statistiques finales:")
    stats = compounder.get_stats()
    
    print(f"   Total trades: {stats['total_trades']}")
    print(f"   Win rate: {stats['win_rate']:.1f}%")
    print(f"   ROI avec compounding: {stats['roi_with_compounding']:.2f}%")
    print(f"   ROI sans compounding: {stats['roi_without_compounding']:.2f}%")
    print(f"   Bénéfice du compounding: +{stats['compound_benefit']:.2f}%")
    print(f"   Capital final: ${stats['current_capital']:.2f}")
    print(f"   Max drawdown: {stats['max_drawdown']:.2f}%")
    
    # Test Kelly sizing
    print(f"\n💡 Kelly Criterion:")
    kelly_size = compounder.calculate_kelly_size()
    print(f"   Taille optimale: {kelly_size:.1f}% du capital")
    
    # Test compound calculation
    print(f"\n💰 Compounding sur profit de $50:")
    
    strategies = ["fixed", "kelly", "volatility_adjusted"]
    
    for strategy in strategies:
        amount = compounder.calculate_compound_amount(
            recent_profit=50.0,
            strategy=strategy,
            volatility_score=40.0
        )
        print(f"   {strategy}: ${amount:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
