#!/usr/bin/env python3
"""
SmartOrder PRO - Market Sentiment Layer
========================================
Analyse du contexte global du marché pour filtrage intelligent des signaux:
- Fear & Greed Index (0-100)
- Volatilité globale (VIX crypto)
- Dominance BTC
- Volume 24h
- Trending coins
- Market regime (BULL/BEAR/NEUTRAL/CHOPPY)

Usage:
    from ai.sentiment import MarketSentiment
    
    sentiment = MarketSentiment()
    
    # Context global
    context = sentiment.get_market_context()
    
    # Filtrer signal selon contexte
    should_trade = sentiment.should_trade_signal(
        signal_confidence=0.85,
        symbol="BTCUSDT"
    )
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time
from enum import Enum


class MarketRegime(Enum):
    """Régimes de marché"""
    BULL = "BULL"           # Tendance haussière forte
    BEAR = "BEAR"           # Tendance baissière forte
    NEUTRAL = "NEUTRAL"     # Range, pas de tendance
    CHOPPY = "CHOPPY"       # Volatile, imprévisible


class RiskLevel(Enum):
    """Niveaux de risque"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class MarketSentiment:
    """Analyse sentiment et contexte marché"""
    
    def __init__(self):
        """Initialise le module sentiment"""
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.last_update = None
    
    def get_fear_greed_index(self) -> Dict[str, any]:
        """
        Récupère Fear & Greed Index
        
        API: https://api.alternative.me/fng/
        
        Returns:
            Dict avec value (0-100) et classification
        """
        # Check cache
        if self._is_cached("fear_greed"):
            return self.cache["fear_greed"]
        
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data and "data" in data and len(data["data"]) > 0:
                latest = data["data"][0]
                value = int(latest["value"])
                classification = latest["value_classification"]
                
                result = {
                    "value": value,
                    "classification": classification,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Classification numérique
                if value <= 25:
                    result["level"] = "Extreme Fear"
                    result["recommendation"] = "BUY opportunity"
                elif value <= 45:
                    result["level"] = "Fear"
                    result["recommendation"] = "Accumulate"
                elif value <= 55:
                    result["level"] = "Neutral"
                    result["recommendation"] = "Normal trading"
                elif value <= 75:
                    result["level"] = "Greed"
                    result["recommendation"] = "Take profits"
                else:
                    result["level"] = "Extreme Greed"
                    result["recommendation"] = "SELL / High risk"
                
                self.cache["fear_greed"] = result
                return result
            
        except Exception as e:
            print(f"⚠️ Erreur Fear & Greed: {e}")
        
        # Fallback neutre
        return {
            "value": 50,
            "classification": "Neutral",
            "level": "Neutral",
            "recommendation": "Normal trading",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_btc_dominance(self) -> float:
        """
        Récupère dominance BTC (%)
        
        API: CoinGecko global data
        
        Returns:
            Dominance BTC en %
        """
        # Check cache
        if self._is_cached("btc_dominance"):
            return self.cache["btc_dominance"]
        
        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data and "data" in data:
                dominance = data["data"]["market_cap_percentage"].get("btc", 50.0)
                
                self.cache["btc_dominance"] = dominance
                return dominance
        
        except Exception as e:
            print(f"⚠️ Erreur BTC dominance: {e}")
        
        # Fallback
        return 50.0
    
    def get_market_volatility(self) -> Dict[str, any]:
        """
        Calcule volatilité globale du marché
        
        Basé sur variations BTC 24h
        
        Returns:
            Dict avec volatility_percent et level
        """
        # Check cache
        if self._is_cached("volatility"):
            return self.cache["volatility"]
        
        try:
            # Utiliser CoinGecko pour prix BTC 24h
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data and "bitcoin" in data:
                change_24h = abs(data["bitcoin"].get("usd_24h_change", 0))
                
                # Classification
                if change_24h < 2:
                    level = "Very Low"
                    risk = RiskLevel.VERY_LOW
                elif change_24h < 4:
                    level = "Low"
                    risk = RiskLevel.LOW
                elif change_24h < 6:
                    level = "Medium"
                    risk = RiskLevel.MEDIUM
                elif change_24h < 10:
                    level = "High"
                    risk = RiskLevel.HIGH
                else:
                    level = "Very High"
                    risk = RiskLevel.VERY_HIGH
                
                result = {
                    "volatility_percent": round(change_24h, 2),
                    "level": level,
                    "risk_level": risk.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                self.cache["volatility"] = result
                return result
        
        except Exception as e:
            print(f"⚠️ Erreur volatility: {e}")
        
        # Fallback
        return {
            "volatility_percent": 3.0,
            "level": "Medium",
            "risk_level": RiskLevel.MEDIUM.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_market_regime(self) -> Dict[str, any]:
        """
        Détermine le régime de marché actuel
        
        Basé sur:
        - Variation BTC 7 jours
        - Fear & Greed
        - Volatilité
        
        Returns:
            Dict avec regime et description
        """
        # Check cache
        if self._is_cached("market_regime"):
            return self.cache["market_regime"]
        
        try:
            # Prix BTC 7 jours
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "7"
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data and "prices" in data:
                prices = [p[1] for p in data["prices"]]
                
                # Variation 7j
                change_7d = ((prices[-1] - prices[0]) / prices[0]) * 100
                
                # Fear & Greed
                fg = self.get_fear_greed_index()
                fg_value = fg["value"]
                
                # Volatilité
                vol = self.get_market_volatility()
                volatility = vol["volatility_percent"]
                
                # Déterminer régime
                if change_7d > 10 and fg_value > 60:
                    regime = MarketRegime.BULL
                    description = "Strong uptrend - Favor LONG positions"
                    strategy = "Trend following, momentum"
                
                elif change_7d < -10 and fg_value < 40:
                    regime = MarketRegime.BEAR
                    description = "Strong downtrend - Favor SHORT positions"
                    strategy = "Reversal, counter-trend"
                
                elif volatility > 8:
                    regime = MarketRegime.CHOPPY
                    description = "High volatility - Reduce position size"
                    strategy = "Scalping, quick profits"
                
                else:
                    regime = MarketRegime.NEUTRAL
                    description = "Range-bound - Trade both directions"
                    strategy = "Mean reversion, range trading"
                
                result = {
                    "regime": regime.value,
                    "description": description,
                    "strategy": strategy,
                    "change_7d": round(change_7d, 2),
                    "confidence": self._calculate_regime_confidence(change_7d, fg_value, volatility),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                self.cache["market_regime"] = result
                return result
        
        except Exception as e:
            print(f"⚠️ Erreur market regime: {e}")
        
        # Fallback
        return {
            "regime": MarketRegime.NEUTRAL.value,
            "description": "Neutral market",
            "strategy": "Normal trading",
            "change_7d": 0.0,
            "confidence": 0.5,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_regime_confidence(
        self,
        change_7d: float,
        fg_value: int,
        volatility: float
    ) -> float:
        """
        Calcule confiance dans le régime détecté
        
        Returns:
            Confiance 0-1
        """
        # Plus la tendance est forte et claire, plus la confiance est haute
        trend_strength = min(abs(change_7d) / 20, 1.0)
        
        # Fear & Greed aux extrêmes = haute confiance
        fg_extreme = max(abs(fg_value - 50) / 50, 0)
        
        # Volatilité élevée = moins de confiance
        volatility_factor = max(0, 1 - (volatility / 15))
        
        confidence = (trend_strength * 0.5 + fg_extreme * 0.3 + volatility_factor * 0.2)
        
        return round(confidence, 2)
    
    def get_market_context(self) -> Dict[str, any]:
        """
        Contexte global du marché (tout en un)
        
        Returns:
            Dict complet avec tous les indicateurs
        """
        fear_greed = self.get_fear_greed_index()
        btc_dominance = self.get_btc_dominance()
        volatility = self.get_market_volatility()
        regime = self.get_market_regime()
        
        # Score de risque global (0-100)
        risk_score = self._calculate_global_risk(
            fear_greed["value"],
            volatility["volatility_percent"],
            regime["regime"]
        )
        
        return {
            "fear_greed": fear_greed,
            "btc_dominance": btc_dominance,
            "volatility": volatility,
            "market_regime": regime,
            "global_risk_score": risk_score,
            "recommendation": self._get_global_recommendation(risk_score),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_global_risk(
        self,
        fg_value: int,
        volatility: float,
        regime: str
    ) -> int:
        """
        Calcule score de risque global (0-100)
        
        0-30: Low risk
        31-60: Medium risk
        61-100: High risk
        
        Returns:
            Risk score 0-100
        """
        # Fear & Greed contribution (30%)
        fg_risk = abs(fg_value - 50) * 0.6  # 0-30
        
        # Volatility contribution (40%)
        vol_risk = min(volatility * 4, 40)  # 0-40
        
        # Regime contribution (30%)
        regime_risk_map = {
            "BULL": 20,
            "NEUTRAL": 30,
            "BEAR": 20,
            "CHOPPY": 50
        }
        regime_risk = regime_risk_map.get(regime, 30)
        
        total_risk = int(fg_risk * 0.3 + vol_risk * 0.4 + regime_risk * 0.3)
        
        return min(total_risk, 100)
    
    def _get_global_recommendation(self, risk_score: int) -> str:
        """Recommandation selon risk score"""
        if risk_score <= 30:
            return "✅ Low risk - Normal trading"
        elif risk_score <= 50:
            return "⚠️ Medium risk - Reduce position sizes"
        elif risk_score <= 70:
            return "🟠 High risk - Trade with caution"
        else:
            return "🔴 Very high risk - Consider staying out"
    
    def should_trade_signal(
        self,
        signal_confidence: float,
        symbol: str,
        min_confidence: float = 0.70,
        max_risk_score: int = 75
    ) -> Dict[str, any]:
        """
        Décide si un signal doit être tradé selon contexte
        
        Args:
            signal_confidence: Confiance du signal (0-1)
            symbol: Symbole tradé
            min_confidence: Confiance minimum requise
            max_risk_score: Risk score maximum accepté
        
        Returns:
            Dict avec decision (True/False) et raisons
        """
        context = self.get_market_context()
        
        risk_score = context["global_risk_score"]
        regime = context["market_regime"]["regime"]
        
        reasons = []
        should_trade = True
        
        # Check 1: Confiance signal
        if signal_confidence < min_confidence:
            should_trade = False
            reasons.append(f"Signal confidence too low: {signal_confidence:.2f} < {min_confidence}")
        
        # Check 2: Risk score
        if risk_score > max_risk_score:
            should_trade = False
            reasons.append(f"Market risk too high: {risk_score}/100")
        
        # Check 3: Extreme Fear & Greed
        fg_value = context["fear_greed"]["value"]
        if fg_value > 85:
            should_trade = False
            reasons.append(f"Extreme Greed detected: {fg_value}/100")
        
        # Check 4: Choppy market
        if regime == "CHOPPY" and signal_confidence < 0.85:
            should_trade = False
            reasons.append("Choppy market - need higher confidence")
        
        # Si OK, ajouter raisons positives
        if should_trade:
            reasons.append("All market conditions favorable")
            reasons.append(f"Risk score: {risk_score}/100 (acceptable)")
            reasons.append(f"Regime: {regime}")
        
        return {
            "should_trade": should_trade,
            "reasons": reasons,
            "signal_confidence": signal_confidence,
            "market_context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _is_cached(self, key: str) -> bool:
        """Vérifie si données en cache et valides"""
        if key not in self.cache:
            return False
        
        # Vérifier âge du cache
        if self.last_update is None:
            return False
        
        age = (datetime.utcnow() - self.last_update).total_seconds()
        
        return age < self.cache_duration
    
    def clear_cache(self):
        """Vide le cache (force refresh)"""
        self.cache = {}
        self.last_update = None
        print("🔄 Cache sentiment vidé")


# ==============================================================================
# EXEMPLE D'UTILISATION
# ==============================================================================

if __name__ == "__main__":
    # Créer instance
    sentiment = MarketSentiment()
    
    print("=" * 70)
    print("MARKET SENTIMENT ANALYSIS")
    print("=" * 70)
    
    # 1. Fear & Greed
    print("\n📊 Fear & Greed Index:")
    fg = sentiment.get_fear_greed_index()
    print(f"   Value: {fg['value']}/100")
    print(f"   Level: {fg['level']}")
    print(f"   Recommendation: {fg['recommendation']}")
    
    # 2. BTC Dominance
    print("\n💎 BTC Dominance:")
    dominance = sentiment.get_btc_dominance()
    print(f"   {dominance:.2f}%")
    
    # 3. Volatilité
    print("\n📈 Market Volatility:")
    vol = sentiment.get_market_volatility()
    print(f"   {vol['volatility_percent']}% (24h)")
    print(f"   Level: {vol['level']}")
    
    # 4. Market Regime
    print("\n🧭 Market Regime:")
    regime = sentiment.get_market_regime()
    print(f"   Regime: {regime['regime']}")
    print(f"   Description: {regime['description']}")
    print(f"   Strategy: {regime['strategy']}")
    print(f"   Confidence: {regime['confidence']}")
    
    # 5. Contexte Global
    print("\n🌍 Global Market Context:")
    context = sentiment.get_market_context()
    print(f"   Risk Score: {context['global_risk_score']}/100")
    print(f"   {context['recommendation']}")
    
    # 6. Test filtrage signal
    print("\n🎯 Signal Filtering Test:")
    decision = sentiment.should_trade_signal(
        signal_confidence=0.85,
        symbol="BTCUSDT"
    )
    print(f"   Should trade: {'✅ YES' if decision['should_trade'] else '❌ NO'}")
    print(f"   Reasons:")
    for reason in decision['reasons']:
        print(f"     - {reason}")
    
    print("\n" + "=" * 70)
    print("✅ Market Sentiment Analysis complet !")
    print("=" * 70)
