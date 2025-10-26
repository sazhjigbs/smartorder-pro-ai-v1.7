#!/usr/bin/env python3
"""
SmartOrder PRO - Intelligent Mode Manager
==========================================
Gestion intelligente des modes de trading avec suggestions IA

Modes disponibles:
- AUTO_SPOT: Trading automatique spot uniquement
- AUTO_FUTURES: Trading automatique futures uniquement
- MANUAL: Mode manuel complet
- HYBRID: IA suggère, utilisateur valide

Usage:
    from ai.mode_manager import TradingModeManager
    
    manager = TradingModeManager()
    
    # Obtenir suggestions
    suggestions = manager.get_suggestions()
    
    # Changer de mode
    manager.set_mode("HYBRID")
    
    # Mode hybride: valider suggestion
    if manager.current_mode == "HYBRID":
        manager.validate_suggestion(suggestion_id, approved=True)
"""

import json
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path

# Import sentiment pour analyse contexte
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.sentiment import MarketSentiment


class TradingMode(Enum):
    """Modes de trading disponibles"""
    AUTO_SPOT = "AUTO_SPOT"
    AUTO_FUTURES = "AUTO_FUTURES"
    MANUAL = "MANUAL"
    HYBRID = "HYBRID"


class MarketStrategy(Enum):
    """Stratégies de trading selon contexte"""
    MOMENTUM_LONG = "Momentum Long"           # Tendance haussière forte
    MOMENTUM_SHORT = "Momentum Short"         # Tendance baissière forte
    RANGE_TRADING = "Range Trading"           # Marché latéral
    SCALPING = "Scalping"                     # Volatilité élevée
    HEDGING = "Hedging"                       # Protection portefeuille
    ACCUMULATION = "Accumulation"             # Fear - accumulation
    TAKE_PROFIT = "Take Profit"               # Greed - prise de bénéfices
    WAIT_AND_SEE = "Wait & See"               # Conditions défavorables


@dataclass
class StrategyConfig:
    """Configuration d'une stratégie"""
    name: str
    description: str
    recommended_coins: List[str]
    timeframes: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH
    position_size_multiplier: float  # 0.5 = 50%, 1.0 = 100%, 1.5 = 150%


@dataclass
class ModeSuggestion:
    """Suggestion de l'IA"""
    id: str
    timestamp: str
    mode: str
    strategy: str
    confidence: float
    reasons: List[str]
    recommended_coins: List[str]
    market_context: Dict[str, Any]
    status: str  # PENDING, APPROVED, REJECTED


class TradingModeManager:
    """Gestionnaire intelligent des modes de trading"""
    
    def __init__(self, db_path: str = "data/mode_manager.db"):
        """
        Initialise le mode manager
        
        Args:
            db_path: Chemin vers base de données SQLite
        """
        self.db_path = db_path
        self.sentiment = MarketSentiment()
        
        # Mode actuel
        self.current_mode = TradingMode.MANUAL
        
        # Historique des suggestions
        self.suggestions_history: List[ModeSuggestion] = []
        
        # Stratégies disponibles
        self.strategies = self._init_strategies()
        
        # Init DB
        self._init_database()
        
        # Charger mode actuel depuis DB
        self._load_current_mode()
    
    def _init_database(self):
        """Initialise la base de données"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table mode actuel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_mode (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                mode TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Table suggestions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL,
                strategy TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasons TEXT NOT NULL,
                recommended_coins TEXT NOT NULL,
                market_context TEXT NOT NULL,
                status TEXT NOT NULL,
                user_action_at TEXT
            )
        """)
        
        # Table historique changements mode
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mode_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                previous_mode TEXT NOT NULL,
                new_mode TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                reason TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_current_mode(self):
        """Charge le mode actuel depuis DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT mode FROM current_mode WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            self.current_mode = TradingMode(row[0])
        else:
            # Premier lancement - mode MANUAL par défaut
            self.current_mode = TradingMode.MANUAL
            cursor.execute(
                "INSERT INTO current_mode (id, mode, updated_at) VALUES (1, ?, ?)",
                (self.current_mode.value, datetime.utcnow().isoformat())
            )
            conn.commit()
        
        conn.close()
    
    def _init_strategies(self) -> Dict[str, StrategyConfig]:
        """Initialise les configurations de stratégies"""
        return {
            MarketStrategy.MOMENTUM_LONG.value: StrategyConfig(
                name="Momentum Long",
                description="Tendance haussière forte - Favoriser positions LONG",
                recommended_coins=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
                timeframes=["15m", "1h", "4h"],
                risk_level="MEDIUM",
                position_size_multiplier=1.2
            ),
            MarketStrategy.MOMENTUM_SHORT.value: StrategyConfig(
                name="Momentum Short",
                description="Tendance baissière forte - Favoriser positions SHORT",
                recommended_coins=["BTCUSDT", "ETHUSDT"],
                timeframes=["15m", "1h"],
                risk_level="HIGH",
                position_size_multiplier=0.8
            ),
            MarketStrategy.RANGE_TRADING.value: StrategyConfig(
                name="Range Trading",
                description="Marché latéral - Trading dans les supports/résistances",
                recommended_coins=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"],
                timeframes=["5m", "15m", "1h"],
                risk_level="LOW",
                position_size_multiplier=1.0
            ),
            MarketStrategy.SCALPING.value: StrategyConfig(
                name="Scalping",
                description="Volatilité élevée - Prises rapides de profits",
                recommended_coins=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                timeframes=["1m", "5m", "15m"],
                risk_level="HIGH",
                position_size_multiplier=0.6
            ),
            MarketStrategy.ACCUMULATION.value: StrategyConfig(
                name="Accumulation",
                description="Fear sur le marché - Opportunité d'accumulation",
                recommended_coins=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"],
                timeframes=["1h", "4h", "1d"],
                risk_level="LOW",
                position_size_multiplier=1.5
            ),
            MarketStrategy.TAKE_PROFIT.value: StrategyConfig(
                name="Take Profit",
                description="Greed sur le marché - Sécuriser profits",
                recommended_coins=["BTCUSDT", "ETHUSDT"],
                timeframes=["15m", "1h"],
                risk_level="LOW",
                position_size_multiplier=0.5
            ),
            MarketStrategy.WAIT_AND_SEE.value: StrategyConfig(
                name="Wait & See",
                description="Conditions défavorables - Attendre meilleure opportunité",
                recommended_coins=[],
                timeframes=[],
                risk_level="VERY_LOW",
                position_size_multiplier=0.0
            )
        }
    
    def get_current_mode(self) -> Dict[str, Any]:
        """Retourne le mode actuel"""
        return {
            "mode": self.current_mode.value,
            "description": self._get_mode_description(self.current_mode),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_mode_description(self, mode: TradingMode) -> str:
        """Description du mode"""
        descriptions = {
            TradingMode.AUTO_SPOT: "Trading automatique Spot uniquement",
            TradingMode.AUTO_FUTURES: "Trading automatique Futures uniquement",
            TradingMode.MANUAL: "Contrôle manuel complet",
            TradingMode.HYBRID: "IA suggère, vous validez"
        }
        return descriptions.get(mode, "Mode inconnu")
    
    def set_mode(self, mode: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Change le mode de trading
        
        Args:
            mode: Nouveau mode (AUTO_SPOT, AUTO_FUTURES, MANUAL, HYBRID)
            reason: Raison du changement (optionnel)
        
        Returns:
            Confirmation du changement
        """
        try:
            new_mode = TradingMode(mode)
        except ValueError:
            return {
                "success": False,
                "error": f"Mode invalide: {mode}",
                "available_modes": [m.value for m in TradingMode]
            }
        
        previous_mode = self.current_mode
        self.current_mode = new_mode
        
        # Sauvegarder en DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update mode actuel
        cursor.execute(
            "UPDATE current_mode SET mode = ?, updated_at = ? WHERE id = 1",
            (new_mode.value, datetime.utcnow().isoformat())
        )
        
        # Ajouter à l'historique
        cursor.execute(
            """INSERT INTO mode_history (previous_mode, new_mode, changed_at, reason)
               VALUES (?, ?, ?, ?)""",
            (previous_mode.value, new_mode.value, datetime.utcnow().isoformat(), reason)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "previous_mode": previous_mode.value,
            "new_mode": new_mode.value,
            "description": self._get_mode_description(new_mode),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_suggestions(self) -> Dict[str, Any]:
        """
        Obtient les suggestions IA basées sur contexte marché
        
        Returns:
            Suggestions de mode, stratégie et coins
        """
        # Analyser contexte marché via sentiment
        market_context = self.sentiment.get_market_context()
        
        # Déterminer stratégie recommandée
        strategy = self._suggest_strategy(market_context)
        
        # Déterminer mode recommandé
        suggested_mode = self._suggest_mode(market_context, strategy)
        
        # Calculer confiance
        confidence = self._calculate_confidence(market_context, strategy)
        
        # Raisons
        reasons = self._generate_reasons(market_context, strategy, suggested_mode)
        
        # Coins recommandés
        strategy_config = self.strategies[strategy.value]
        recommended_coins = strategy_config.recommended_coins
        
        return {
            "current_mode": self.current_mode.value,
            "suggested_mode": suggested_mode.value,
            "strategy": {
                "name": strategy.value,
                "description": strategy_config.description,
                "risk_level": strategy_config.risk_level,
                "position_size_multiplier": strategy_config.position_size_multiplier,
                "timeframes": strategy_config.timeframes
            },
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "recommended_coins": recommended_coins,
            "market_context": market_context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _suggest_strategy(self, context: Dict[str, Any]) -> MarketStrategy:
        """Suggère stratégie selon contexte marché"""
        regime = context["market_regime"]["regime"]
        fg_value = context["fear_greed"]["value"]
        volatility = context["volatility"]["volatility_percent"]
        risk_score = context["global_risk_score"]
        
        # Extreme Fear -> Accumulation
        if fg_value <= 25:
            return MarketStrategy.ACCUMULATION
        
        # Extreme Greed -> Take Profit
        if fg_value >= 75:
            return MarketStrategy.TAKE_PROFIT
        
        # Risk trop élevé -> Wait & See
        if risk_score > 80:
            return MarketStrategy.WAIT_AND_SEE
        
        # Choppy -> Scalping
        if regime == "CHOPPY" or volatility > 8:
            return MarketStrategy.SCALPING
        
        # Bull -> Momentum Long
        if regime == "BULL":
            return MarketStrategy.MOMENTUM_LONG
        
        # Bear -> Momentum Short
        if regime == "BEAR":
            return MarketStrategy.MOMENTUM_SHORT
        
        # Neutral -> Range Trading
        return MarketStrategy.RANGE_TRADING
    
    def _suggest_mode(self, context: Dict[str, Any], strategy: MarketStrategy) -> TradingMode:
        """Suggère mode selon contexte et stratégie"""
        risk_score = context["global_risk_score"]
        
        # Risk très élevé -> Manual ou Hybrid
        if risk_score > 70:
            return TradingMode.HYBRID
        
        # Wait & See -> Manual
        if strategy == MarketStrategy.WAIT_AND_SEE:
            return TradingMode.MANUAL
        
        # Conditions favorables -> AUTO selon stratégie
        if strategy in [MarketStrategy.ACCUMULATION, MarketStrategy.MOMENTUM_LONG]:
            return TradingMode.AUTO_SPOT
        
        if strategy in [MarketStrategy.MOMENTUM_SHORT, MarketStrategy.SCALPING]:
            return TradingMode.AUTO_FUTURES
        
        # Par défaut -> Hybrid (sécurité)
        return TradingMode.HYBRID
    
    def _calculate_confidence(self, context: Dict[str, Any], strategy: MarketStrategy) -> float:
        """Calcule confiance dans la suggestion"""
        regime_confidence = context["market_regime"]["confidence"]
        risk_score = context["global_risk_score"]
        
        # Risk élevé = moins de confiance
        risk_factor = max(0, 1 - (risk_score / 100))
        
        # Confiance finale
        confidence = (regime_confidence * 0.6 + risk_factor * 0.4)
        
        return min(confidence, 0.99)
    
    def _generate_reasons(
        self,
        context: Dict[str, Any],
        strategy: MarketStrategy,
        mode: TradingMode
    ) -> List[str]:
        """Génère raisons de la suggestion"""
        reasons = []
        
        regime = context["market_regime"]["regime"]
        fg = context["fear_greed"]
        risk_score = context["global_risk_score"]
        
        # Régime
        reasons.append(f"Marché {regime}: {context['market_regime']['description']}")
        
        # Fear & Greed
        reasons.append(f"Fear & Greed: {fg['value']}/100 ({fg['level']})")
        
        # Risk score
        reasons.append(f"Risk Score: {risk_score}/100")
        
        # Stratégie
        strategy_config = self.strategies[strategy.value]
        reasons.append(f"Stratégie recommandée: {strategy_config.description}")
        
        # Mode
        reasons.append(f"Mode suggéré: {self._get_mode_description(mode)}")
        
        return reasons
    
    def create_suggestion(self) -> ModeSuggestion:
        """Crée une nouvelle suggestion (pour mode HYBRID)"""
        suggestions = self.get_suggestions()
        
        suggestion = ModeSuggestion(
            id=f"SUGG_{int(datetime.utcnow().timestamp())}",
            timestamp=datetime.utcnow().isoformat(),
            mode=suggestions["suggested_mode"],
            strategy=suggestions["strategy"]["name"],
            confidence=suggestions["confidence"],
            reasons=suggestions["reasons"],
            recommended_coins=suggestions["recommended_coins"],
            market_context=suggestions["market_context"],
            status="PENDING"
        )
        
        # Sauvegarder en DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO suggestions 
               (id, timestamp, mode, strategy, confidence, reasons, recommended_coins, market_context, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                suggestion.id,
                suggestion.timestamp,
                suggestion.mode,
                suggestion.strategy,
                suggestion.confidence,
                json.dumps(suggestion.reasons),
                json.dumps(suggestion.recommended_coins),
                json.dumps(suggestion.market_context),
                suggestion.status
            )
        )
        
        conn.commit()
        conn.close()
        
        return suggestion
    
    def validate_suggestion(self, suggestion_id: str, approved: bool) -> Dict[str, Any]:
        """
        Valide ou rejette une suggestion (mode HYBRID)
        
        Args:
            suggestion_id: ID de la suggestion
            approved: True = approuvé, False = rejeté
        
        Returns:
            Résultat de la validation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupérer suggestion
        cursor.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {
                "success": False,
                "error": f"Suggestion {suggestion_id} introuvable"
            }
        
        # Update status
        new_status = "APPROVED" if approved else "REJECTED"
        cursor.execute(
            "UPDATE suggestions SET status = ?, user_action_at = ? WHERE id = ?",
            (new_status, datetime.utcnow().isoformat(), suggestion_id)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "suggestion_id": suggestion_id,
            "approved": approved,
            "status": new_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_mode_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère l'historique des changements de mode"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT previous_mode, new_mode, changed_at, reason 
               FROM mode_history 
               ORDER BY id DESC 
               LIMIT ?""",
            (limit,)
        )
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "previous_mode": row[0],
                "new_mode": row[1],
                "changed_at": row[2],
                "reason": row[3]
            })
        
        conn.close()
        return history


# ==============================================================================
# EXEMPLE D'UTILISATION
# ==============================================================================

if __name__ == "__main__":
    manager = TradingModeManager()
    
    print("=" * 70)
    print("🎯 TRADING MODE MANAGER")
    print("=" * 70)
    
    # Mode actuel
    print("\n📍 Mode actuel:")
    current = manager.get_current_mode()
    print(f"   {current['mode']} - {current['description']}")
    
    # Suggestions IA
    print("\n🤖 Suggestions IA:")
    suggestions = manager.get_suggestions()
    print(f"   Mode suggéré: {suggestions['suggested_mode']}")
    print(f"   Stratégie: {suggestions['strategy']['name']}")
    print(f"   Confiance: {suggestions['confidence']}")
    print(f"   Coins recommandés: {', '.join(suggestions['recommended_coins'])}")
    print(f"\n   Raisons:")
    for reason in suggestions['reasons']:
        print(f"     - {reason}")
    
    print("\n" + "=" * 70)
    print("✅ Mode Manager opérationnel !")
    print("=" * 70)
