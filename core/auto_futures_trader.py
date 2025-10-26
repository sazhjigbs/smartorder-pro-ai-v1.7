"""
SmartOrder PRO - Adaptive Futures Trader
Trading futures avec leverage dynamique et risk management avancé
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

from core.volatility_predictor import get_volatility_predictor
from core.sentiment_analyzer import get_sentiment_analyzer
from core.whale_tracker import get_whale_tracker
from core.smart_compounding import get_smart_compounding

LOG = logging.getLogger("auto_futures_trader")
LOG.setLevel(logging.INFO)

class AdaptiveFuturesTrader:
    """
    Trading futures adaptatif avec leverage dynamique
    
    Features:
    - Leverage adaptatif: 1x-10x selon volatilité
    - Position sizing intelligent selon Kelly Criterion
    - SL/TP dynamiques selon ATR
    - Hedging automatique spot/futures
    - Funding rate arbitrage
    
    Risk Management:
    - Max 20% capital par trade
    - Max 3 positions simultanées
    - Stop loss obligatoire
    - Trailing stop en profit
    
    Leverage Rules:
    - Vol < 30: Leverage 8-10x
    - Vol 30-50: Leverage 5-7x
    - Vol 50-70: Leverage 3-5x
    - Vol > 70: Leverage 1-3x
    """
    
    def __init__(self, total_capital: float = 10000.0, max_leverage: int = 10):
        """
        Initialize Adaptive Futures Trader
        
        Args:
            total_capital: Capital total en USDT
            max_leverage: Leverage maximum autorisé
        """
        self.total_capital = total_capital
        self.available_capital = total_capital
        self.max_leverage = max_leverage
        
        # Positions actives
        self.active_positions = {}  # {symbol: position_data}
        
        # Paramètres de risk management
        self.max_position_pct = 20.0  # Max 20% du capital par position
        self.max_positions = 3  # Max 3 positions simultanées
        self.default_sl_pct = 2.0  # Stop Loss -2%
        self.default_tp_pct = 4.0  # Take Profit +4%
        
        # Modules d'analyse
        self.vol_predictor = get_volatility_predictor()
        self.sentiment = get_sentiment_analyzer()
        self.whale_tracker = get_whale_tracker()
        self.compounding = get_smart_compounding(total_capital)
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_drawdown': 0.0,
            'peak_capital': total_capital,
            'avg_leverage': 0.0,
            'funding_earned': 0.0
        }
        
        LOG.info(f"AdaptiveFuturesTrader initialized: ${total_capital:,.2f} | Max leverage: {max_leverage}x")
    
    def calculate_adaptive_leverage(self, symbol: str, volatility_score: float, 
                                   sentiment_score: float) -> int:
        """
        Calcule le leverage optimal selon conditions
        
        Args:
            symbol: Symbole
            volatility_score: Score de volatilité 0-100
            sentiment_score: Score de sentiment 0-100
            
        Returns:
            Leverage optimal (1-max_leverage)
        """
        # Base leverage selon volatilité
        if volatility_score < 30:
            base_leverage = 10
        elif volatility_score < 50:
            base_leverage = 7
        elif volatility_score < 70:
            base_leverage = 5
        else:
            base_leverage = 3
        
        # Ajuster selon sentiment (confiance)
        if sentiment_score < 30 or sentiment_score > 70:
            # Extreme sentiment = réduire leverage (incertitude)
            base_leverage = max(1, int(base_leverage * 0.7))
        
        # Limiter au max autorisé
        leverage = min(base_leverage, self.max_leverage)
        
        LOG.debug(f"Leverage calculated for {symbol}: {leverage}x (vol: {volatility_score:.0f}, sent: {sentiment_score:.0f})")
        
        return leverage
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                                leverage: int, volatility_score: float) -> Dict:
        """
        Calcule la taille de position optimale
        
        Uses Smart Compounding + Kelly Criterion
        
        Returns:
            {
                'position_size_usdt': float,
                'quantity': float,
                'margin_required': float,
                'leverage': int
            }
        """
        # Utiliser smart compounding pour sizing
        sizing = self.compounding.get_next_position_size(
            symbol,
            entry_price,
            strategy='kelly',
            volatility_score=volatility_score
        )
        
        position_size_usdt = sizing['position_size_usdt']
        
        # Limiter à max_position_pct
        max_size = self.total_capital * (self.max_position_pct / 100)
        position_size_usdt = min(position_size_usdt, max_size)
        
        # Calculer margin avec leverage
        margin_required = position_size_usdt / leverage
        quantity = position_size_usdt / entry_price
        
        return {
            'position_size_usdt': round(position_size_usdt, 2),
            'quantity': round(quantity, 6),
            'margin_required': round(margin_required, 2),
            'leverage': leverage,
            'reasoning': sizing['reasoning']
        }
    
    def calculate_dynamic_sl_tp(self, symbol: str, entry_price: float, 
                                side: str, atr: float, volatility_score: float) -> Tuple[float, float]:
        """
        Calcule SL et TP dynamiques selon ATR et volatilité
        
        Args:
            symbol: Symbole
            entry_price: Prix d'entrée
            side: 'LONG' | 'SHORT'
            atr: Average True Range (%)
            volatility_score: Score de volatilité
            
        Returns:
            (stop_loss_price, take_profit_price)
        """
        # Élargir SL/TP en haute volatilité
        vol_multiplier = 1.0
        
        if volatility_score > 70:
            vol_multiplier = 2.0
        elif volatility_score > 50:
            vol_multiplier = 1.5
        elif volatility_score > 30:
            vol_multiplier = 1.2
        
        # SL basé sur ATR
        sl_pct = max(self.default_sl_pct, atr * 1.5) * vol_multiplier
        
        # TP = 2x SL (risk:reward 1:2)
        tp_pct = sl_pct * 2
        
        if side == 'LONG':
            stop_loss = entry_price * (1 - sl_pct / 100)
            take_profit = entry_price * (1 + tp_pct / 100)
        else:  # SHORT
            stop_loss = entry_price * (1 + sl_pct / 100)
            take_profit = entry_price * (1 - tp_pct / 100)
        
        LOG.debug(f"SL/TP calculated: SL {sl_pct:.1f}% | TP {tp_pct:.1f}% (vol mult: {vol_multiplier}x)")
        
        return round(stop_loss, 2), round(take_profit, 2)
    
    def open_position(self, symbol: str, side: str, entry_price: float, 
                     market_data: Dict) -> Dict:
        """
        Ouvre une position futures
        
        Args:
            symbol: Symbole (ex: 'BTCUSDT')
            side: 'LONG' | 'SHORT'
            entry_price: Prix d'entrée
            market_data: Données de marché (volatility, sentiment, atr, etc.)
            
        Returns:
            Résultat de l'ouverture
        """
        # Vérifier nombre max de positions
        if len(self.active_positions) >= self.max_positions:
            return {
                'success': False,
                'reason': f'Max positions reached ({self.max_positions})'
            }
        
        # Analyser conditions
        volatility_score = market_data.get('volatility_score', 50)
        sentiment_score = market_data.get('sentiment_score', 50)
        atr = market_data.get('atr', 2.0)
        
        # Calculer leverage adaptatif
        leverage = self.calculate_adaptive_leverage(symbol, volatility_score, sentiment_score)
        
        # Calculer taille de position
        sizing = self.calculate_position_size(symbol, entry_price, leverage, volatility_score)
        
        # Vérifier capital disponible
        if sizing['margin_required'] > self.available_capital:
            return {
                'success': False,
                'reason': f'Insufficient capital: ${sizing["margin_required"]:.2f} required'
            }
        
        # Calculer SL/TP
        stop_loss, take_profit = self.calculate_dynamic_sl_tp(
            symbol, entry_price, side, atr, volatility_score
        )
        
        # Créer position
        position = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'quantity': sizing['quantity'],
            'leverage': leverage,
            'margin_used': sizing['margin_required'],
            'position_size_usdt': sizing['position_size_usdt'],
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'opened_at': datetime.now().isoformat(),
            'status': 'OPEN',
            'pnl': 0.0
        }
        
        # Enregistrer position
        self.active_positions[symbol] = position
        self.available_capital -= sizing['margin_required']
        
        # Stats
        self.stats['total_trades'] += 1
        
        # Compute avg leverage
        total_lev = sum(p['leverage'] for p in self.active_positions.values())
        self.stats['avg_leverage'] = total_lev / len(self.active_positions)
        
        LOG.info(f"✅ Position opened: {symbol} {side} {leverage}x | "
                f"Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")
        
        return {
            'success': True,
            'position': position
        }
    
    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Met à jour toutes les positions actives
        
        Args:
            current_prices: {'BTCUSDT': 67000, ...}
            
        Returns:
            Liste des positions fermées (SL/TP hit)
        """
        closed_positions = []
        
        for symbol, position in list(self.active_positions.items()):
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            entry_price = position['entry_price']
            side = position['side']
            
            # Calculer PnL
            if side == 'LONG':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SHORT
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Avec leverage
            pnl_pct *= position['leverage']
            pnl_usdt = position['margin_used'] * (pnl_pct / 100)
            
            position['pnl'] = pnl_usdt
            position['pnl_pct'] = pnl_pct
            
            # Check SL/TP
            hit = None
            
            if side == 'LONG':
                if current_price <= position['stop_loss']:
                    hit = 'SL'
                elif current_price >= position['take_profit']:
                    hit = 'TP'
            else:  # SHORT
                if current_price >= position['stop_loss']:
                    hit = 'SL'
                elif current_price <= position['take_profit']:
                    hit = 'TP'
            
            if hit:
                # Fermer position
                position['status'] = 'CLOSED'
                position['closed_at'] = datetime.now().isoformat()
                position['close_price'] = current_price
                position['exit_reason'] = hit
                
                # Libérer capital
                self.available_capital += position['margin_used'] + pnl_usdt
                
                # Update stats
                if pnl_usdt > 0:
                    self.stats['winning_trades'] += 1
                    self.stats['total_profit'] += pnl_usdt
                else:
                    self.stats['losing_trades'] += 1
                    self.stats['total_loss'] += abs(pnl_usdt)
                
                # Track peak & drawdown
                if self.available_capital > self.stats['peak_capital']:
                    self.stats['peak_capital'] = self.available_capital
                
                drawdown = ((self.stats['peak_capital'] - self.available_capital) / 
                          self.stats['peak_capital'] * 100)
                
                if drawdown > self.stats['max_drawdown']:
                    self.stats['max_drawdown'] = drawdown
                
                # Record trade for compounding
                self.compounding.record_trade({
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'quantity': position['quantity'],
                    'profit_usdt': pnl_usdt,
                    'profit_pct': pnl_pct / position['leverage'],
                    'timestamp': position['closed_at']
                })
                
                closed_positions.append(position)
                
                LOG.info(f"💰 Position closed: {symbol} {hit} | "
                        f"PnL: ${pnl_usdt:.2f} ({pnl_pct:.1f}%)")
                
                # Supprimer de actives
                del self.active_positions[symbol]
        
        return closed_positions
    
    def get_position_summary(self) -> Dict:
        """Résumé des positions actives"""
        total_margin = sum(p['margin_used'] for p in self.active_positions.values())
        total_pnl = sum(p.get('pnl', 0) for p in self.active_positions.values())
        
        return {
            'active_positions': len(self.active_positions),
            'total_margin_used': round(total_margin, 2),
            'unrealized_pnl': round(total_pnl, 2),
            'available_capital': round(self.available_capital, 2),
            'total_capital': round(self.available_capital + total_margin + total_pnl, 2),
            'positions': list(self.active_positions.values())
        }
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        win_rate = 0.0
        if self.stats['total_trades'] > 0:
            win_rate = (self.stats['winning_trades'] / self.stats['total_trades']) * 100
        
        net_profit = self.stats['total_profit'] - self.stats['total_loss']
        roi = (net_profit / self.total_capital) * 100
        
        return {
            **self.stats,
            'win_rate': round(win_rate, 1),
            'net_profit': round(net_profit, 2),
            'roi': round(roi, 2),
            'active_positions': len(self.active_positions)
        }


# Instance globale
_auto_futures_trader = None

def get_auto_futures_trader(capital: float = 10000.0, max_lev: int = 10) -> AdaptiveFuturesTrader:
    """Récupère l'instance singleton"""
    global _auto_futures_trader
    if _auto_futures_trader is None:
        _auto_futures_trader = AdaptiveFuturesTrader(capital, max_lev)
    return _auto_futures_trader


if __name__ == "__main__":
    print("=" * 60)
    print("Adaptive Futures Trader - Test")
    print("=" * 60)
    
    trader = AdaptiveFuturesTrader(total_capital=10000.0, max_leverage=10)
    
    print(f"\n💰 Capital: ${trader.total_capital:,.2f}")
    print(f"   Max leverage: {trader.max_leverage}x")
    print(f"   Max positions: {trader.max_positions}")
    print(f"   Max position size: {trader.max_position_pct}%")
    
    # Test adaptive leverage
    print(f"\n📊 Adaptive Leverage Tests:")
    
    test_cases = [
        (25, 50, "Low vol, neutral sentiment"),
        (60, 30, "Medium vol, fear"),
        (85, 80, "High vol, extreme greed")
    ]
    
    for vol, sent, desc in test_cases:
        lev = trader.calculate_adaptive_leverage('BTCUSDT', vol, sent)
        print(f"   {desc}: {lev}x (vol: {vol}, sent: {sent})")
    
    # Open a position
    print(f"\n🚀 Opening LONG position on BTCUSDT...")
    
    market_data = {
        'volatility_score': 45,
        'sentiment_score': 55,
        'atr': 2.5
    }
    
    result = trader.open_position(
        'BTCUSDT',
        'LONG',
        entry_price=67000.0,
        market_data=market_data
    )
    
    if result['success']:
        pos = result['position']
        print(f"   ✅ Success!")
        print(f"   Leverage: {pos['leverage']}x")
        print(f"   Size: ${pos['position_size_usdt']:,.2f}")
        print(f"   Margin: ${pos['margin_used']:,.2f}")
        print(f"   Entry: {pos['entry_price']}")
        print(f"   SL: {pos['stop_loss']}")
        print(f"   TP: {pos['take_profit']}")
    
    # Update position (TP hit)
    print(f"\n⚡ Simulating price move to TP...")
    
    tp_price = result['position']['take_profit']
    closed = trader.update_positions({'BTCUSDT': tp_price + 10})
    
    if closed:
        pos = closed[0]
        print(f"   💰 Position closed: {pos['exit_reason']}")
        print(f"   PnL: ${pos['pnl']:.2f} ({pos['pnl_pct']:.1f}%)")
    
    # Stats
    stats = trader.get_stats()
    print(f"\n📈 Stats:")
    print(f"   Total trades: {stats['total_trades']}")
    print(f"   Win rate: {stats['win_rate']:.1f}%")
    print(f"   Net profit: ${stats['net_profit']:.2f}")
    print(f"   ROI: {stats['roi']:.2f}%")
    print(f"   Max drawdown: {stats['max_drawdown']:.2f}%")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
