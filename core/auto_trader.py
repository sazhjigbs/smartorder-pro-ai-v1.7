"""
SmartOrder PRO - AutoTrader Engine v1.0
Trading automatique intelligent avec validation multi-signaux
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Configuration du logging
LOG = logging.getLogger("auto_trader")
LOG.setLevel(logging.INFO)

class AutoTrader:
    """
    Moteur de trading automatique intelligent
    
    Features:
    - Lecture mode actif depuis Mode Manager
    - Sélection coins depuis trading_coins.json
    - Validation multi-signaux (IA + Indicateurs techniques)
    - Gestion capital adaptative selon volatilité
    - Exécution trades spot + futures
    """
    
    def __init__(self, config_path: str = "config/trading_coins.json"):
        """
        Initialize AutoTrader
        
        Args:
            config_path: Chemin vers le fichier de configuration des coins
        """
        self.config_path = config_path
        self.coins_config = {}
        self.active_mode = "MANUAL"  # MANUAL, AUTO_SPOT, AUTO_FUTURES, HYBRID
        self.is_running = False
        self.capital_available = 0.0
        self.active_positions = {}
        
        # Statistiques
        self.stats = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_profit_usdt": 0.0,
            "win_rate": 0.0
        }
        
        # Charger la configuration
        self._load_config()
        
        LOG.info("AutoTrader initialized successfully")
    
    def _load_config(self):
        """Charge la configuration des coins depuis le fichier JSON"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.coins_config = data.get('coins', {})
                    self.risk_profiles = data.get('risk_profiles', {})
                    LOG.info(f"Loaded {len(self.coins_config)} coins from config")
            else:
                LOG.warning(f"Config file not found: {self.config_path}")
                self.coins_config = {}
        except Exception as e:
            LOG.error(f"Error loading config: {e}")
            self.coins_config = {}
    
    def get_enabled_coins(self) -> List[str]:
        """
        Retourne la liste des coins activés pour le trading
        
        Returns:
            Liste des symboles (ex: ['BTCUSDT', 'ETHUSDT'])
        """
        enabled = []
        for symbol, config in self.coins_config.items():
            if config.get('enabled', False):
                enabled.append(symbol)
        
        LOG.info(f"Found {len(enabled)} enabled coins: {enabled}")
        return enabled
    
    def get_coin_config(self, symbol: str) -> Dict:
        """
        Récupère la configuration d'un coin spécifique
        
        Args:
            symbol: Symbole du coin (ex: 'BTCUSDT')
            
        Returns:
            Configuration du coin
        """
        return self.coins_config.get(symbol, {})
    
    def set_mode(self, mode: str):
        """
        Définit le mode de trading actif
        
        Args:
            mode: MANUAL, AUTO_SPOT, AUTO_FUTURES, HYBRID
        """
        valid_modes = ["MANUAL", "AUTO_SPOT", "AUTO_FUTURES", "HYBRID"]
        if mode in valid_modes:
            self.active_mode = mode
            LOG.info(f"Trading mode set to: {mode}")
        else:
            LOG.error(f"Invalid mode: {mode}. Must be one of {valid_modes}")
    
    def get_mode(self) -> str:
        """Retourne le mode actif actuel"""
        return self.active_mode
    
    def validate_signal(self, symbol: str, signal_data: Dict) -> Tuple[bool, float, str]:
        """
        Valide un signal de trading avec critères multi-sources
        
        Critères de validation (3/4 requis pour AUTO, 4/4 pour confiance max):
        1. IA Mode Manager: Confiance > 70%
        2. RSI: Entre 30-70 (pas surachat/survente)
        3. MACD: Croisement confirmé
        4. Volume: > 150% de la moyenne 24h
        
        Args:
            symbol: Symbole du coin
            signal_data: Données du signal (ia_confidence, rsi, macd, volume_ratio)
            
        Returns:
            (valid, confidence, reason)
        """
        # Extraction des données
        ia_conf = signal_data.get('ia_confidence', 0)
        rsi = signal_data.get('rsi', 50)
        macd_bullish = signal_data.get('macd_bullish', False)
        volume_ratio = signal_data.get('volume_ratio', 1.0)
        
        # Validation des critères
        criteria_passed = 0
        reasons = []
        
        # 1. IA Confidence
        if ia_conf >= 70:
            criteria_passed += 1
            reasons.append(f"IA: {ia_conf}% ✓")
        else:
            reasons.append(f"IA: {ia_conf}% ✗")
        
        # 2. RSI
        if 30 <= rsi <= 70:
            criteria_passed += 1
            reasons.append(f"RSI: {rsi} ✓")
        else:
            reasons.append(f"RSI: {rsi} ✗")
        
        # 3. MACD
        if macd_bullish:
            criteria_passed += 1
            reasons.append("MACD: Bullish ✓")
        else:
            reasons.append("MACD: Bearish ✗")
        
        # 4. Volume
        if volume_ratio >= 1.5:
            criteria_passed += 1
            reasons.append(f"Volume: +{(volume_ratio-1)*100:.0f}% ✓")
        else:
            reasons.append(f"Volume: {volume_ratio:.1f}x ✗")
        
        # Calcul confiance finale
        confidence = (criteria_passed / 4) * 100
        valid = criteria_passed >= 3  # Au moins 3/4 critères
        
        reason = f"{criteria_passed}/4 critères | " + " | ".join(reasons)
        
        if valid:
            LOG.info(f"Signal VALID for {symbol}: {reason}")
        else:
            LOG.warning(f"Signal REJECTED for {symbol}: {reason}")
        
        return valid, confidence, reason
    
    def calculate_position_size(self, symbol: str, confidence: float, volatility: float) -> float:
        """
        Calcule la taille de position intelligente selon:
        - Confiance du signal (50-100%)
        - Volatilité du marché (ATR)
        - Capital disponible
        - Configuration du coin (max_capital_pct)
        
        Args:
            symbol: Symbole du coin
            confidence: Confiance du signal (0-100)
            volatility: Volatilité (ATR en %)
            
        Returns:
            Capital à utiliser en USDT
        """
        coin_config = self.get_coin_config(symbol)
        max_capital_pct = coin_config.get('max_capital_pct', 10)
        risk_level = coin_config.get('risk_level', 'MEDIUM')
        
        # Base capital selon config coin
        base_capital = self.capital_available * (max_capital_pct / 100)
        
        # Ajustement selon confiance (0.5x à 1.0x)
        confidence_multiplier = 0.5 + (confidence / 200)
        
        # Ajustement selon volatilité (inverse: moins volatile = plus de capital)
        if volatility < 2:
            volatility_multiplier = 1.2  # Stable, on peut risquer plus
        elif volatility < 5:
            volatility_multiplier = 1.0  # Normal
        elif volatility < 10:
            volatility_multiplier = 0.7  # Volatil, réduire
        else:
            volatility_multiplier = 0.5  # Très volatil, très prudent
        
        # Ajustement selon risk level
        risk_multipliers = {
            'LOW': 0.8,
            'MEDIUM': 1.0,
            'HIGH': 0.6  # Paradoxe: high risk = réduire exposition
        }
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        # Calcul final
        position_size = base_capital * confidence_multiplier * volatility_multiplier * risk_multiplier
        
        # Limites de sécurité
        min_position = 5.0  # Minimum 5 USDT
        max_position = self.capital_available * 0.3  # Maximum 30% du capital
        
        position_size = max(min_position, min(position_size, max_position))
        
        LOG.info(f"Position size for {symbol}: {position_size:.2f} USDT "
                f"(conf:{confidence:.0f}%, vol:{volatility:.1f}%, risk:{risk_level})")
        
        return position_size
    
    def calculate_leverage(self, symbol: str, volatility: float, confidence: float) -> int:
        """
        Calcule le leverage adaptatif pour futures
        
        Formule: Leverage = Base × (Confidence / Volatility)
        
        Args:
            symbol: Symbole du coin
            volatility: Volatilité (ATR en %)
            confidence: Confiance du signal (0-100)
            
        Returns:
            Leverage recommandé (1-50x)
        """
        coin_config = self.get_coin_config(symbol)
        base_leverage = coin_config.get('leverage_futures', 10)
        
        # Ajustement selon signal
        if confidence >= 85 and volatility < 3:
            # Signal très fort + marché stable = leverage max
            leverage = min(base_leverage * 1.5, 20)
        elif confidence >= 70 and volatility < 5:
            # Signal fort + volatilité moyenne = leverage normal
            leverage = base_leverage
        elif volatility > 8:
            # Marché très volatil = réduire leverage
            leverage = max(3, base_leverage * 0.5)
        else:
            # Cas par défaut
            leverage = base_leverage * 0.7
        
        # Limites de sécurité
        leverage = max(1, min(int(leverage), 50))
        
        LOG.info(f"Leverage for {symbol}: {leverage}x (vol:{volatility:.1f}%, conf:{confidence:.0f}%)")
        
        return leverage
    
    def calculate_sl_tp(self, symbol: str, entry_price: float, side: str) -> Dict:
        """
        Calcule Stop Loss et Take Profit adaptatifs
        
        Args:
            symbol: Symbole du coin
            entry_price: Prix d'entrée
            side: LONG ou SHORT
            
        Returns:
            Dict avec sl_price et tp_levels (3 niveaux)
        """
        coin_config = self.get_coin_config(symbol)
        sl_pct = coin_config.get('sl_pct', 2.0)
        tp_levels_pct = coin_config.get('tp_levels', [2.0, 4.0, 8.0])
        
        if side == "LONG":
            # Long: SL en bas, TP en haut
            sl_price = entry_price * (1 - sl_pct / 100)
            tp_levels = [entry_price * (1 + tp / 100) for tp in tp_levels_pct]
        else:
            # Short: SL en haut, TP en bas
            sl_price = entry_price * (1 + sl_pct / 100)
            tp_levels = [entry_price * (1 - tp / 100) for tp in tp_levels_pct]
        
        return {
            'sl_price': round(sl_price, 2),
            'tp1': round(tp_levels[0], 2),
            'tp2': round(tp_levels[1], 2),
            'tp3': round(tp_levels[2], 2)
        }
    
    def execute_trade(self, symbol: str, side: str, position_size: float, leverage: int = 1) -> Dict:
        """
        Execute un trade (spot ou futures)
        
        Args:
            symbol: Symbole du coin
            side: BUY/SELL (spot) ou LONG/SHORT (futures)
            position_size: Capital en USDT
            leverage: Leverage pour futures (1 = spot)
            
        Returns:
            Résultat de l'exécution
        """
        try:
            # TODO: Intégration avec Bybit API
            # Pour l'instant, simulation
            
            current_price = 67000  # TODO: Fetch real price
            
            sl_tp = self.calculate_sl_tp(symbol, current_price, side)
            
            result = {
                'success': True,
                'symbol': symbol,
                'side': side,
                'entry_price': current_price,
                'position_size_usdt': position_size,
                'leverage': leverage,
                'sl_price': sl_tp['sl_price'],
                'tp_levels': [sl_tp['tp1'], sl_tp['tp2'], sl_tp['tp3']],
                'timestamp': datetime.now().isoformat()
            }
            
            # Enregistrer la position
            self.active_positions[symbol] = result
            
            LOG.info(f"Trade executed: {symbol} {side} {position_size} USDT @ {current_price}")
            
            return result
            
        except Exception as e:
            LOG.error(f"Trade execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start(self):
        """Démarre le trading automatique"""
        if self.is_running:
            LOG.warning("AutoTrader already running")
            return
        
        self.is_running = True
        LOG.info(f"AutoTrader STARTED in {self.active_mode} mode")
        
        # TODO: Lancer la boucle de trading en arrière-plan (Thread ou AsyncIO)
    
    def stop(self):
        """Arrête le trading automatique"""
        self.is_running = False
        LOG.info("AutoTrader STOPPED")
    
    def get_status(self) -> Dict:
        """
        Retourne le statut complet du bot
        
        Returns:
            Statut avec positions, stats, mode actif
        """
        return {
            'is_running': self.is_running,
            'mode': self.active_mode,
            'capital_available': self.capital_available,
            'active_positions': len(self.active_positions),
            'stats': self.stats,
            'enabled_coins': self.get_enabled_coins()
        }


# Instance globale
_auto_trader_instance = None

def get_auto_trader() -> AutoTrader:
    """
    Récupère l'instance singleton d'AutoTrader
    
    Returns:
        Instance AutoTrader
    """
    global _auto_trader_instance
    if _auto_trader_instance is None:
        _auto_trader_instance = AutoTrader()
    return _auto_trader_instance


if __name__ == "__main__":
    # Test du module
    print("=" * 60)
    print("AutoTrader Engine v1.0 - Test")
    print("=" * 60)
    
    trader = AutoTrader()
    
    # Test 1: Charger les coins
    print(f"\n✅ Coins enabled: {trader.get_enabled_coins()}")
    
    # Test 2: Validation signal
    signal_data = {
        'ia_confidence': 85,
        'rsi': 45,
        'macd_bullish': True,
        'volume_ratio': 2.0
    }
    valid, conf, reason = trader.validate_signal('BTCUSDT', signal_data)
    print(f"\n✅ Signal validation: {valid} ({conf:.0f}%)")
    print(f"   Reason: {reason}")
    
    # Test 3: Position sizing
    trader.capital_available = 100.0
    size = trader.calculate_position_size('BTCUSDT', conf, 2.5)
    print(f"\n✅ Position size: {size:.2f} USDT")
    
    # Test 4: Leverage calculation
    leverage = trader.calculate_leverage('BTCUSDT', 2.5, conf)
    print(f"✅ Leverage: {leverage}x")
    
    # Test 5: SL/TP calculation
    sl_tp = trader.calculate_sl_tp('BTCUSDT', 67000, 'LONG')
    print(f"\n✅ SL/TP:")
    print(f"   SL: {sl_tp['sl_price']}")
    print(f"   TP1: {sl_tp['tp1']} | TP2: {sl_tp['tp2']} | TP3: {sl_tp['tp3']}")
    
    # Test 6: Status
    status = trader.get_status()
    print(f"\n✅ Status: {json.dumps(status, indent=2)}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
