#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Signal Validator
=====================================
Validation multi-layer des signaux de trading
by MAIGA ABOUBACAR

4 Niveaux de validation:
1. AI Confidence > 70%
2. Technical Indicators (RSI, MACD, Volume)
3. Market Regime compatible
4. Risk Limits respectées
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

LOG = logging.getLogger("signal_validator")
LOG.setLevel(logging.INFO)

class ValidationLevel(Enum):
    """Niveaux de validation"""
    LEVEL_1_AI = "ai_confidence"
    LEVEL_2_TECHNICAL = "technical_indicators"
    LEVEL_3_REGIME = "market_regime"
    LEVEL_4_RISK = "risk_limits"

class MarketRegime(Enum):
    """Régimes de marché"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    RANGING = "ranging"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"

@dataclass
class ValidationResult:
    """Résultat de validation"""
    passed: bool
    level: ValidationLevel
    score: float  # 0-100
    reason: str
    details: Dict

class SignalValidator:
    """
    Validation multi-layer des signaux
    
    4 niveaux obligatoires:
    - Level 1: AI Confidence
    - Level 2: Technical Indicators
    - Level 3: Market Regime
    - Level 4: Risk Limits
    """
    
    def __init__(self, config: Dict = None):
        """Initialize Signal Validator"""
        self.config = config or self._default_config()
        LOG.info("✅ Signal Validator initialized")
    
    def _default_config(self) -> Dict:
        """Configuration par défaut"""
        return {
            "level_1_ai": {
                "min_confidence": 0.70,
                "weight": 30
            },
            "level_2_technical": {
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "min_volume_ratio": 1.2,
                "macd_required": True,
                "weight": 25
            },
            "level_3_regime": {
                "allowed_regimes": ["uptrend", "sideways", "ranging"],
                "weight": 15
            },
            "level_4_risk": {
                "max_position_size_usd": 500,
                "max_daily_trades": 20,
                "max_open_positions": 5,
                "min_risk_reward_ratio": 1.5,
                "weight": 30
            },
            "min_total_score": 70
        }
    
    def validate_signal(self, signal: Dict, market_data: Dict, risk_data: Dict) -> Tuple[bool, List[ValidationResult]]:
        """
        Valide un signal sur les 4 niveaux
        
        Args:
            signal: Signal de trading
            market_data: Données de marché
            risk_data: Données de risque
        
        Returns:
            (passed, results) - True si valide, liste des résultats par niveau
        """
        results = []
        
        # Level 1: AI Confidence
        level_1 = self._validate_level_1_ai(signal)
        results.append(level_1)
        
        # Level 2: Technical Indicators
        level_2 = self._validate_level_2_technical(signal, market_data)
        results.append(level_2)
        
        # Level 3: Market Regime
        level_3 = self._validate_level_3_regime(signal, market_data)
        results.append(level_3)
        
        # Level 4: Risk Limits
        level_4 = self._validate_level_4_risk(signal, risk_data)
        results.append(level_4)
        
        # Calculate total score
        total_score = self._calculate_total_score(results)
        
        # Validation finale
        all_passed = all(r.passed for r in results)
        score_passed = total_score >= self.config["min_total_score"]
        
        final_passed = all_passed and score_passed
        
        if final_passed:
            LOG.info(f"✅ Signal VALIDATED | Score: {total_score:.1f}/100 | {signal.get('coin', 'Unknown')}")
        else:
            failed_levels = [r.level.value for r in results if not r.passed]
            LOG.warning(f"❌ Signal REJECTED | Score: {total_score:.1f}/100 | Failed: {failed_levels}")
        
        return final_passed, results
    
    def _validate_level_1_ai(self, signal: Dict) -> ValidationResult:
        """
        Level 1: AI Confidence Validation
        
        Vérifie que la confiance IA est suffisante
        """
        ai_confidence = signal.get("ai_confidence", 0.0)
        min_confidence = self.config["level_1_ai"]["min_confidence"]
        
        passed = ai_confidence >= min_confidence
        
        # Calculate score
        if passed:
            score = min(100, (ai_confidence / min_confidence) * 100)
        else:
            score = (ai_confidence / min_confidence) * 100
        
        return ValidationResult(
            passed=passed,
            level=ValidationLevel.LEVEL_1_AI,
            score=score,
            reason=f"AI confidence: {ai_confidence:.1%} (min: {min_confidence:.1%})",
            details={
                "ai_confidence": ai_confidence,
                "min_required": min_confidence
            }
        )
    
    def _validate_level_2_technical(self, signal: Dict, market_data: Dict) -> ValidationResult:
        """
        Level 2: Technical Indicators Validation
        
        Vérifie RSI, MACD, Volume
        """
        checks = []
        details = {}
        
        # RSI check
        rsi = market_data.get("rsi", 50)
        side = signal.get("side", "buy")
        
        if side == "buy":
            rsi_ok = rsi < self.config["level_2_technical"]["rsi_overbought"]
            checks.append(rsi_ok)
            details["rsi"] = {"value": rsi, "status": "ok" if rsi_ok else "overbought"}
        else:
            rsi_ok = rsi > self.config["level_2_technical"]["rsi_oversold"]
            checks.append(rsi_ok)
            details["rsi"] = {"value": rsi, "status": "ok" if rsi_ok else "oversold"}
        
        # Volume check
        volume_ratio = market_data.get("volume_ratio", 1.0)
        min_volume_ratio = self.config["level_2_technical"]["min_volume_ratio"]
        volume_ok = volume_ratio >= min_volume_ratio
        checks.append(volume_ok)
        details["volume"] = {
            "ratio": volume_ratio,
            "min_required": min_volume_ratio,
            "status": "ok" if volume_ok else "low"
        }
        
        # MACD check
        macd_signal = market_data.get("macd_signal", "neutral")
        if self.config["level_2_technical"]["macd_required"]:
            if side == "buy":
                macd_ok = macd_signal in ["bullish", "buy"]
            else:
                macd_ok = macd_signal in ["bearish", "sell"]
            checks.append(macd_ok)
            details["macd"] = {"signal": macd_signal, "status": "ok" if macd_ok else "mismatch"}
        
        # Calculate score
        passed_checks = sum(checks)
        total_checks = len(checks)
        score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        passed = score >= 60  # Au moins 60% des checks passent
        
        return ValidationResult(
            passed=passed,
            level=ValidationLevel.LEVEL_2_TECHNICAL,
            score=score,
            reason=f"Technical checks: {passed_checks}/{total_checks} passed",
            details=details
        )
    
    def _validate_level_3_regime(self, signal: Dict, market_data: Dict) -> ValidationResult:
        """
        Level 3: Market Regime Validation
        
        Vérifie que le régime de marché est compatible
        """
        current_regime = market_data.get("regime", "unknown")
        allowed_regimes = self.config["level_3_regime"]["allowed_regimes"]
        
        passed = current_regime in allowed_regimes
        
        # Calculate score based on regime strength
        regime_strength = market_data.get("regime_strength", 0.5)  # 0-1
        if passed:
            score = regime_strength * 100
        else:
            score = 0
        
        return ValidationResult(
            passed=passed,
            level=ValidationLevel.LEVEL_3_REGIME,
            score=score,
            reason=f"Market regime: {current_regime} ({'allowed' if passed else 'not allowed'})",
            details={
                "current_regime": current_regime,
                "allowed_regimes": allowed_regimes,
                "regime_strength": regime_strength
            }
        )
    
    def _validate_level_4_risk(self, signal: Dict, risk_data: Dict) -> ValidationResult:
        """
        Level 4: Risk Limits Validation
        
        Vérifie tous les risques
        """
        checks = []
        details = {}
        
        # Position size check
        position_size = signal.get("position_size_usd", 0)
        max_size = self.config["level_4_risk"]["max_position_size_usd"]
        size_ok = position_size <= max_size
        checks.append(size_ok)
        details["position_size"] = {
            "value": position_size,
            "max": max_size,
            "status": "ok" if size_ok else "too_large"
        }
        
        # Daily trades check
        daily_trades = risk_data.get("daily_trades", 0)
        max_daily = self.config["level_4_risk"]["max_daily_trades"]
        trades_ok = daily_trades < max_daily
        checks.append(trades_ok)
        details["daily_trades"] = {
            "count": daily_trades,
            "max": max_daily,
            "status": "ok" if trades_ok else "limit_reached"
        }
        
        # Open positions check
        open_positions = risk_data.get("open_positions", 0)
        max_open = self.config["level_4_risk"]["max_open_positions"]
        positions_ok = open_positions < max_open
        checks.append(positions_ok)
        details["open_positions"] = {
            "count": open_positions,
            "max": max_open,
            "status": "ok" if positions_ok else "limit_reached"
        }
        
        # Risk/Reward ratio check
        risk_reward = signal.get("risk_reward_ratio", 0)
        min_rr = self.config["level_4_risk"]["min_risk_reward_ratio"]
        rr_ok = risk_reward >= min_rr
        checks.append(rr_ok)
        details["risk_reward"] = {
            "ratio": risk_reward,
            "min_required": min_rr,
            "status": "ok" if rr_ok else "too_low"
        }
        
        # Calculate score
        passed_checks = sum(checks)
        total_checks = len(checks)
        score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        passed = score == 100  # TOUS les checks doivent passer pour le risk
        
        return ValidationResult(
            passed=passed,
            level=ValidationLevel.LEVEL_4_RISK,
            score=score,
            reason=f"Risk checks: {passed_checks}/{total_checks} passed",
            details=details
        )
    
    def _calculate_total_score(self, results: List[ValidationResult]) -> float:
        """
        Calcule le score total pondéré
        
        Args:
            results: Liste des résultats de validation
        
        Returns:
            Score total (0-100)
        """
        weights = {
            ValidationLevel.LEVEL_1_AI: self.config["level_1_ai"]["weight"],
            ValidationLevel.LEVEL_2_TECHNICAL: self.config["level_2_technical"]["weight"],
            ValidationLevel.LEVEL_3_REGIME: self.config["level_3_regime"]["weight"],
            ValidationLevel.LEVEL_4_RISK: self.config["level_4_risk"]["weight"]
        }
        
        total_score = 0.0
        total_weight = sum(weights.values())
        
        for result in results:
            weight = weights.get(result.level, 0)
            weighted_score = (result.score * weight) / 100
            total_score += weighted_score
        
        # Normalize to 0-100
        return (total_score / total_weight) * 100 if total_weight > 0 else 0
    
    def get_validation_report(self, results: List[ValidationResult]) -> str:
        """
        Génère un rapport de validation lisible
        
        Args:
            results: Résultats de validation
        
        Returns:
            Rapport formaté
        """
        report = []
        report.append("=" * 60)
        report.append("SIGNAL VALIDATION REPORT")
        report.append("=" * 60)
        
        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report.append(f"\n{status} | Level {result.level.value.upper()}")
            report.append(f"Score: {result.score:.1f}/100")
            report.append(f"Reason: {result.reason}")
            
            if result.details:
                report.append("Details:")
                for key, value in result.details.items():
                    report.append(f"  - {key}: {value}")
        
        total_score = self._calculate_total_score(results)
        report.append("\n" + "=" * 60)
        report.append(f"TOTAL SCORE: {total_score:.1f}/100")
        report.append(f"STATUS: {'✅ VALIDATED' if all(r.passed for r in results) else '❌ REJECTED'}")
        report.append("=" * 60)
        
        return "\n".join(report)


# Singleton
_validator = None

def get_signal_validator() -> SignalValidator:
    """Get singleton instance"""
    global _validator
    if _validator is None:
        _validator = SignalValidator()
    return _validator


if __name__ == "__main__":
    # Test
    print("🔥 Testing Signal Validator...")
    
    validator = SignalValidator()
    
    # Test signal
    signal = {
        "coin": "BTC",
        "side": "buy",
        "ai_confidence": 0.85,
        "position_size_usd": 200,
        "risk_reward_ratio": 2.5
    }
    
    market_data = {
        "rsi": 45,
        "volume_ratio": 1.5,
        "macd_signal": "bullish",
        "regime": "uptrend",
        "regime_strength": 0.8
    }
    
    risk_data = {
        "daily_trades": 5,
        "open_positions": 2
    }
    
    # Validate
    passed, results = validator.validate_signal(signal, market_data, risk_data)
    
    # Print report
    print("\n" + validator.get_validation_report(results))
    
    print(f"\n{'✅ Signal VALIDATED' if passed else '❌ Signal REJECTED'}")
