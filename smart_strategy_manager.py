#!/usr/bin/env python3
"""
🧠 SMART STRATEGY MANAGER
========================
by MAIGA ABOUBACAR

Gestion intelligente des stratégies par mode avec IA:
- Suggestion automatique selon market regime
- Toggle ON/OFF par stratégie
- Exécution automatique des stratégies adaptées
- Support SPOT/FUTURES/HYBRIDE/MANUEL
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Import modules existants
from core.market_regime_detector import MarketRegimeDetector
from core.signal_validator import SignalValidator

LOG = logging.getLogger("smart_strategy_manager")
LOG.setLevel(logging.INFO)

class SmartStrategyManager:
    """
    Gestionnaire intelligent de stratégies
    
    Features:
    - Charge configuration depuis strategies_config_complete.json
    - Détecte market regime
    - Suggère meilleures stratégies
    - Execute automatiquement selon user selection
    """
    
    def __init__(self, config_path: str = "strategies_config_complete.json"):
        """Initialize Smart Strategy Manager"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Market regime detector
        self.regime_detector = MarketRegimeDetector()
        
        # Signal validator
        self.signal_validator = SignalValidator()
        
        # État actuel
        self.current_mode = None
        self.current_regime = None
        self.active_strategies = {}
        
        LOG.info("✅ Smart Strategy Manager initialized")
    
    def _load_config(self) -> Dict:
        """Charge la configuration des stratégies"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            LOG.info(f"✅ Loaded strategies config v{config.get('version', '1.0')}")
            return config
        except Exception as e:
            LOG.error(f"❌ Error loading config: {e}")
            return {}
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            LOG.info("✅ Config saved")
        except Exception as e:
            LOG.error(f"❌ Error saving config: {e}")
    
    def set_mode(self, mode: str) -> bool:
        """
        Active un mode de trading
        
        Args:
            mode: SPOT, FUTURES, HYBRIDE, ou MANUEL
        
        Returns:
            True si succès
        """
        mode = mode.upper()
        
        if mode not in self.config['modes']:
            LOG.error(f"❌ Mode invalide: {mode}")
            return False
        
        # Désactiver ancien mode
        if self.current_mode:
            self.config['modes'][self.current_mode]['active'] = False
        
        # Activer nouveau mode
        self.config['modes'][mode]['active'] = True
        self.current_mode = mode
        
        self._save_config()
        
        LOG.info(f"✅ Mode activé: {mode}")
        return True
    
    def toggle_strategy(self, mode: str, strategy_id: str, enabled: bool) -> bool:
        """
        Active/Désactive une stratégie
        
        Args:
            mode: SPOT, FUTURES, HYBRIDE, MANUEL
            strategy_id: ID de la stratégie
            enabled: True pour activer, False pour désactiver
        
        Returns:
            True si succès
        """
        mode = mode.upper()
        
        if mode not in self.config['modes']:
            return False
        
        if strategy_id not in self.config['modes'][mode]['strategies']:
            return False
        
        self.config['modes'][mode]['strategies'][strategy_id]['enabled'] = enabled
        self._save_config()
        
        status = "activée" if enabled else "désactivée"
        LOG.info(f"✅ Stratégie {strategy_id} {status} en mode {mode}")
        
        return True
    
    def detect_market_regime(self, market_data: Dict) -> Dict:
        """
        Détecte le régime de marché actuel
        
        Args:
            market_data: Données de marché (price, indicators, etc.)
        
        Returns:
            Dict avec regime, strength, recommendations
        """
        # Utilise le Market Regime Detector
        indicators = {
            'sma_20': market_data.get('sma_20', market_data.get('current_price', 0)),
            'sma_50': market_data.get('sma_50', market_data.get('current_price', 0)),
            'volatility': market_data.get('volatility', 0)
        }
        
        regime_data = self.regime_detector.detect_regime(market_data, indicators)
        
        self.current_regime = regime_data['regime']
        
        # Ajouter recommandations
        regime_data['recommendations'] = self._get_regime_recommendations(regime_data['regime'])
        
        return regime_data
    
    def _get_regime_recommendations(self, regime: str) -> Dict:
        """
        Retourne les stratégies recommandées pour un régime
        
        Args:
            regime: uptrend, downtrend, sideways, ranging, volatile
        
        Returns:
            Dict avec recommendations par mode
        """
        mappings = self.config.get('market_regime_mappings', {})
        
        if regime not in mappings:
            return {}
        
        return {
            'description': mappings[regime]['description'],
            'strategies': mappings[regime]['recommended_strategies'],
            'leverage_adjustment': mappings[regime]['leverage_adjustment']
        }
    
    def get_ai_suggestions(self, mode: str, market_data: Dict) -> List[Dict]:
        """
        Retourne les suggestions IA de stratégies
        
        Args:
            mode: SPOT, FUTURES, HYBRIDE, MANUEL
            market_data: Données de marché
        
        Returns:
            Liste de stratégies suggérées avec score
        """
        mode = mode.upper()
        
        # Détecte regime
        regime_data = self.detect_market_regime(market_data)
        current_regime = regime_data['regime']
        
        # Récupère stratégies du mode
        mode_strategies = self.config['modes'][mode]['strategies']
        
        # Récupère recommandations regime
        recommended = regime_data['recommendations'].get('strategies', {}).get(mode, [])
        
        suggestions = []
        
        for strategy_id, strategy_config in mode_strategies.items():
            # Check si compatible avec regime actuel
            compatible_regimes = strategy_config.get('market_regimes', [])
            
            score = 0
            reason = []
            
            # Score basé sur compatibilité regime
            if current_regime in compatible_regimes or 'all' in compatible_regimes:
                score += 40
                reason.append(f"Compatible {current_regime}")
            
            # Score basé sur recommandation IA
            if strategy_id in recommended:
                score += 40
                reason.append(f"Recommandé pour {current_regime}")
            
            # Score basé sur priorité
            priority = strategy_config.get('priority', 999)
            priority_score = max(0, 20 - (priority * 2))
            score += priority_score
            
            # Check conditions
            conditions_met = self._check_strategy_conditions(
                strategy_config.get('conditions', {}),
                market_data
            )
            
            if conditions_met:
                reason.append("Conditions remplies")
            else:
                score -= 20
                reason.append("Conditions partielles")
            
            suggestions.append({
                'strategy_id': strategy_id,
                'name': strategy_config['name'],
                'score': min(100, max(0, score)),
                'enabled': strategy_config.get('enabled', False),
                'reason': ' | '.join(reason),
                'priority': priority,
                'recommended': strategy_id in recommended
            })
        
        # Tri par score desc
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return suggestions
    
    def _check_strategy_conditions(self, conditions: Dict, market_data: Dict) -> bool:
        """
        Vérifie si les conditions d'une stratégie sont remplies
        
        Args:
            conditions: Conditions de la stratégie
            market_data: Données de marché
        
        Returns:
            True si conditions OK
        """
        if not conditions:
            return True
        
        for key, limits in conditions.items():
            value = market_data.get(key, 0)
            
            if isinstance(limits, dict):
                if 'min' in limits and value < limits['min']:
                    return False
                if 'max' in limits and value > limits['max']:
                    return False
            elif isinstance(limits, bool):
                if market_data.get(key, False) != limits:
                    return False
        
        return True
    
    def get_active_strategies_for_execution(self, mode: str, market_data: Dict) -> List[Dict]:
        """
        Retourne les stratégies activées ET compatibles avec le marché actuel
        
        Args:
            mode: SPOT, FUTURES, HYBRIDE, MANUEL
            market_data: Données de marché
        
        Returns:
            Liste de stratégies à executer
        """
        mode = mode.upper()
        
        # Détecte regime
        regime_data = self.detect_market_regime(market_data)
        current_regime = regime_data['regime']
        
        mode_strategies = self.config['modes'][mode]['strategies']
        
        executable = []
        
        for strategy_id, strategy_config in mode_strategies.items():
            # Must be enabled
            if not strategy_config.get('enabled', False):
                continue
            
            # Check regime compatibility
            compatible_regimes = strategy_config.get('market_regimes', [])
            if current_regime not in compatible_regimes and 'all' not in compatible_regimes:
                LOG.info(f"⏭️ {strategy_id} skipped - incompatible avec {current_regime}")
                continue
            
            # Check conditions
            if not self._check_strategy_conditions(strategy_config.get('conditions', {}), market_data):
                LOG.info(f"⏭️ {strategy_id} skipped - conditions non remplies")
                continue
            
            executable.append({
                'strategy_id': strategy_id,
                'name': strategy_config['name'],
                'config': strategy_config['config'],
                'priority': strategy_config.get('priority', 999)
            })
        
        # Tri par priorité
        executable.sort(key=lambda x: x['priority'])
        
        # Limite au nombre max concurrent
        max_concurrent = self.config['strategy_selector']['max_concurrent_strategies']
        executable = executable[:max_concurrent]
        
        LOG.info(f"✅ {len(executable)} stratégies à executer en mode {mode}")
        
        return executable
    
    def get_dashboard_state(self) -> Dict:
        """
        Retourne l'état complet pour le dashboard
        
        Returns:
            Dict avec modes, strategies, regime, suggestions
        """
        return {
            'current_mode': self.current_mode,
            'current_regime': self.current_regime,
            'modes': self.config['modes'],
            'strategy_selector': self.config['strategy_selector'],
            'timestamp': datetime.now().isoformat()
        }


# Singleton
_manager = None

def get_strategy_manager() -> SmartStrategyManager:
    """Retourne instance singleton du Strategy Manager"""
    global _manager
    if _manager is None:
        _manager = SmartStrategyManager()
    return _manager


if __name__ == '__main__':
    # Test
    manager = get_strategy_manager()
    
    # Test mode switch
    manager.set_mode('SPOT')
    
    # Test market data
    market_data = {
        'current_price': 50000,
        'sma_20': 49000,
        'sma_50': 48000,
        'volatility': 2.5,
        'rsi': 45,
        'adx': 30,
        'volume_ratio': 1.8
    }
    
    # Détecte regime
    regime = manager.detect_market_regime(market_data)
    print(f"\n🔍 Market Regime: {regime['regime']} (strength: {regime['strength']})")
    
    # Suggestions IA
    suggestions = manager.get_ai_suggestions('SPOT', market_data)
    print(f"\n🤖 AI Suggestions pour SPOT:")
    for s in suggestions[:5]:
        print(f"  {'✅' if s['enabled'] else '⬜'} {s['name']}: {s['score']}/100 - {s['reason']}")
    
    # Stratégies executables
    executable = manager.get_active_strategies_for_execution('SPOT', market_data)
    print(f"\n▶️ Stratégies à executer: {len(executable)}")
    for e in executable:
        print(f"  - {e['name']} (priority: {e['priority']})")
