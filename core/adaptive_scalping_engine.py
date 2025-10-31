#!/usr/bin/env python3
"""
⚡ ADAPTIVE SCALPING ENGINE
===========================
by MAIGA ABOUBACAR

Scalping intelligent qui s'adapte automatiquement à:
- Volatilité du marché (ATR)
- Volume
- Régime de marché
- Flash crashes

Features:
- Timeframe dynamique selon volatilité
- TP/SL adaptatifs
- Flash crash hunter
- Auto-compound des profits
"""

import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

LOG = logging.getLogger("adaptive_scalping")
LOG.setLevel(logging.INFO)

class VolatilityRegime(Enum):
    """Régimes de volatilité"""
    LOW = "low"          # ATR < 1%
    MEDIUM = "medium"    # ATR 1-3%
    HIGH = "high"        # ATR 3-5%
    EXTREME = "extreme"  # ATR > 5%

@dataclass
class ScalpingConfig:
    """Configuration dynamique du scalping"""
    timeframe: str
    take_profit_percent: float
    stop_loss_percent: float
    position_size_percent: float
    max_trades_per_hour: int
    leverage: int = 1
    
class AdaptiveScalpingEngine:
    """
    Scalping Engine qui s'adapte automatiquement
    
    Ajustements selon volatilité:
    - LOW: TF 5m/15m, TP 0.5%, SL 0.3%, Size normal
    - MEDIUM: TF 3m/10m, TP 1%, SL 0.5%, Size normal
    - HIGH: TF 1m/5m, TP 2%, SL 1%, Size réduit (-50%)
    - EXTREME: PAUSE trading ou Flash Crash Hunter
    """
    
    def __init__(self, initial_capital: float = 1000):
        """Initialize Adaptive Scalping Engine"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        self.trades_history = []
        self.current_regime = VolatilityRegime.MEDIUM
        
        # Flash crash detection
        self.flash_crash_enabled = True
        self.flash_crash_threshold = -5.0  # -5% en < 1min
        
        # Auto-compound
        self.auto_compound = True
        self.compound_threshold = 0.05  # Réinvestit après +5%
        
        # Stats
        self.total_profit = 0.0
        self.win_rate = 0.0
        self.trades_count = 0
        
        LOG.info("✅ Adaptive Scalping Engine initialized")
    
    def detect_volatility_regime(self, market_data: Dict) -> VolatilityRegime:
        """
        Détecte le régime de volatilité actuel
        
        Args:
            market_data: Dict avec 'atr', 'volatility', etc.
        
        Returns:
            VolatilityRegime
        """
        atr = market_data.get('atr', 0)
        price = market_data.get('price', 1)
        
        # ATR en pourcentage du prix
        atr_percent = (atr / price) * 100 if price > 0 else 0
        
        if atr_percent < 1.0:
            regime = VolatilityRegime.LOW
        elif atr_percent < 3.0:
            regime = VolatilityRegime.MEDIUM
        elif atr_percent < 5.0:
            regime = VolatilityRegime.HIGH
        else:
            regime = VolatilityRegime.EXTREME
        
        if regime != self.current_regime:
            LOG.info(f"🔄 Volatility regime changed: {self.current_regime.value} → {regime.value}")
            self.current_regime = regime
        
        return regime
    
    def get_adaptive_config(self, regime: VolatilityRegime) -> ScalpingConfig:
        """
        Retourne config adaptée au régime de volatilité
        
        Args:
            regime: Régime de volatilité
        
        Returns:
            ScalpingConfig adapté
        """
        configs = {
            VolatilityRegime.LOW: ScalpingConfig(
                timeframe="5m",
                take_profit_percent=0.5,
                stop_loss_percent=0.3,
                position_size_percent=10.0,
                max_trades_per_hour=8,
                leverage=1
            ),
            VolatilityRegime.MEDIUM: ScalpingConfig(
                timeframe="3m",
                take_profit_percent=1.0,
                stop_loss_percent=0.5,
                position_size_percent=10.0,
                max_trades_per_hour=12,
                leverage=1
            ),
            VolatilityRegime.HIGH: ScalpingConfig(
                timeframe="1m",
                take_profit_percent=2.0,
                stop_loss_percent=1.0,
                position_size_percent=5.0,  # Réduit de 50%
                max_trades_per_hour=20,
                leverage=1
            ),
            VolatilityRegime.EXTREME: ScalpingConfig(
                timeframe="1m",
                take_profit_percent=1.0,
                stop_loss_percent=0.5,
                position_size_percent=2.0,  # Très réduit
                max_trades_per_hour=5,
                leverage=1
            )
        }
        
        return configs.get(regime, configs[VolatilityRegime.MEDIUM])
    
    def detect_flash_crash(self, price_history: List[float]) -> bool:
        """
        Détecte un flash crash (chute rapide > 5%)
        
        Args:
            price_history: Liste des derniers prix (1min)
        
        Returns:
            True si flash crash détecté
        """
        if not self.flash_crash_enabled or len(price_history) < 2:
            return False
        
        # Compare prix actuel vs prix il y a 1min
        current_price = price_history[-1]
        old_price = price_history[0]
        
        drop_percent = ((current_price - old_price) / old_price) * 100
        
        if drop_percent < self.flash_crash_threshold:
            LOG.warning(f"🚨 FLASH CRASH DETECTED: {drop_percent:.2f}% drop!")
            return True
        
        return False
    
    def should_hunt_flash_crash(self, market_data: Dict) -> bool:
        """
        Décide si on doit "hunter" le flash crash (buy the dip)
        
        Args:
            market_data: Données de marché
        
        Returns:
            True si opportunité flash crash
        """
        # Conditions pour hunter:
        # 1. Flash crash détecté
        # 2. Volume élevé (confirmation)
        # 3. RSI oversold
        
        volume_ratio = market_data.get('volume_ratio', 1.0)
        rsi = market_data.get('rsi', 50)
        
        if volume_ratio > 2.0 and rsi < 30:
            LOG.info("🎯 Flash crash hunting opportunity!")
            return True
        
        return False
    
    def generate_scalp_signal(self, market_data: Dict) -> Optional[Dict]:
        """
        Génère signal de scalping adaptatif
        
        Args:
            market_data: Données de marché
        
        Returns:
            Signal dict ou None
        """
        # Détecte régime
        regime = self.detect_volatility_regime(market_data)
        config = self.get_adaptive_config(regime)
        
        # Si EXTREME volatilité, check flash crash
        if regime == VolatilityRegime.EXTREME:
            price_history = market_data.get('price_history', [])
            if self.detect_flash_crash(price_history):
                if self.should_hunt_flash_crash(market_data):
                    return {
                        'action': 'BUY',
                        'type': 'FLASH_CRASH_HUNT',
                        'config': ScalpingConfig(
                            timeframe="1m",
                            take_profit_percent=1.0,  # Quick flip
                            stop_loss_percent=0.5,
                            position_size_percent=3.0,
                            max_trades_per_hour=1,
                            leverage=1
                        ),
                        'reason': 'Flash crash hunting',
                        'confidence': 0.85
                    }
                else:
                    LOG.warning("⏸️ PAUSE trading - extreme volatility without opportunity")
                    return None
        
        # Signal normal basé sur indicateurs
        rsi = market_data.get('rsi', 50)
        macd_hist = market_data.get('macd_hist', 0)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        signal = None
        confidence = 0.0
        
        # BUY signal
        if rsi < 35 and macd_hist > 0 and volume_ratio > 1.2:
            signal = 'BUY'
            confidence = 0.75
        
        # SELL signal
        elif rsi > 65 and macd_hist < 0 and volume_ratio > 1.2:
            signal = 'SELL'
            confidence = 0.75
        
        if signal:
            return {
                'action': signal,
                'type': 'NORMAL_SCALP',
                'config': config,
                'reason': f'{regime.value} volatility scalp',
                'confidence': confidence
            }
        
        return None
    
    def execute_scalp_trade(self, signal: Dict, current_price: float) -> Dict:
        """
        Execute un trade de scalping (paper ou real)
        
        Args:
            signal: Signal généré
            current_price: Prix actuel
        
        Returns:
            Trade result dict
        """
        config = signal['config']
        action = signal['action']
        
        # Calculate position size avec auto-compound
        if self.auto_compound and self.total_profit > 0:
            # Réinvestit les profits si > threshold
            profit_percent = (self.total_profit / self.initial_capital) * 100
            if profit_percent >= self.compound_threshold * 100:
                capital_to_use = self.current_capital
                LOG.info(f"💰 Auto-compounding: using ${capital_to_use:.2f}")
            else:
                capital_to_use = self.initial_capital
        else:
            capital_to_use = self.current_capital
        
        position_size_usd = capital_to_use * (config.position_size_percent / 100)
        amount = position_size_usd / current_price
        
        # Calculate TP/SL prices
        if action == 'BUY':
            tp_price = current_price * (1 + config.take_profit_percent / 100)
            sl_price = current_price * (1 - config.stop_loss_percent / 100)
        else:
            tp_price = current_price * (1 - config.take_profit_percent / 100)
            sl_price = current_price * (1 + config.stop_loss_percent / 100)
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'entry_price': current_price,
            'amount': amount,
            'position_size_usd': position_size_usd,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'config': config,
            'status': 'OPEN'
        }
        
        self.positions.append(trade)
        
        LOG.info(f"✅ Scalp trade executed: {action} {amount:.6f} @ ${current_price:.2f}")
        LOG.info(f"   TP: ${tp_price:.2f} | SL: ${sl_price:.2f}")
        
        return trade
    
    def check_positions(self, current_price: float) -> List[Dict]:
        """
        Vérifie les positions ouvertes et close si TP/SL atteint
        
        Args:
            current_price: Prix actuel
        
        Returns:
            Liste des positions fermées
        """
        closed_positions = []
        
        for pos in self.positions[:]:
            if pos['status'] != 'OPEN':
                continue
            
            tp_hit = False
            sl_hit = False
            
            if pos['action'] == 'BUY':
                tp_hit = current_price >= pos['tp_price']
                sl_hit = current_price <= pos['sl_price']
            else:
                tp_hit = current_price <= pos['tp_price']
                sl_hit = current_price >= pos['sl_price']
            
            if tp_hit or sl_hit:
                # Close position
                pnl = (current_price - pos['entry_price']) * pos['amount']
                if pos['action'] == 'SELL':
                    pnl = -pnl
                
                pos['status'] = 'CLOSED'
                pos['exit_price'] = current_price
                pos['pnl'] = pnl
                pos['exit_reason'] = 'TP' if tp_hit else 'SL'
                pos['closed_at'] = datetime.now().isoformat()
                
                self.current_capital += pnl
                self.total_profit += pnl
                self.trades_count += 1
                
                closed_positions.append(pos)
                self.trades_history.append(pos)
                
                LOG.info(f"{'✅' if pnl > 0 else '❌'} Position closed: {pos['exit_reason']} | PnL: ${pnl:+.2f}")
        
        # Remove closed positions
        self.positions = [p for p in self.positions if p['status'] == 'OPEN']
        
        # Update win rate
        if self.trades_count > 0:
            wins = len([t for t in self.trades_history if t.get('pnl', 0) > 0])
            self.win_rate = (wins / self.trades_count) * 100
        
        return closed_positions
    
    def get_stats(self) -> Dict:
        """Retourne statistiques du scalping"""
        return {
            'current_capital': self.current_capital,
            'initial_capital': self.initial_capital,
            'total_profit': self.total_profit,
            'profit_percent': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'win_rate': self.win_rate,
            'trades_count': self.trades_count,
            'open_positions': len(self.positions),
            'current_regime': self.current_regime.value
        }


# Singleton
_engine = None

def get_adaptive_scalping_engine() -> AdaptiveScalpingEngine:
    """Retourne instance singleton"""
    global _engine
    if _engine is None:
        _engine = AdaptiveScalpingEngine()
    return _engine
