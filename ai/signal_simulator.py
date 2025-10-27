#!/usr/bin/env python3
"""
🎯 SAFELOGIC SmartOrder PRO - AI Signal Simulator
=================================================
Générateur de signaux de test pour simuler l'IA
by MAIGA ABOUBACAR

Modes:
- RANDOM: Signaux aléatoires bullish/bearish
- BULLISH: Toujours bullish (pour tester long)
- BEARISH: Toujours bearish (pour tester short)
- REALISTIC: Simule comportement réaliste avec tendances

Usage:
    from ai.signal_simulator import SignalSimulator
    
    sim = SignalSimulator(mode="REALISTIC")
    signal = sim.generate_signal("BTCUSDT")
    
    print(signal)
    # {
    #   "symbol": "BTCUSDT",
    #   "bias": "bullish",
    #   "confidence": 0.78,
    #   "action": "BUY",
    #   "reasons": ["Strong momentum", "Volume spike"],
    #   "timestamp": "2025-01-27T00:00:00Z"
    # }
"""

import random
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class SimulationMode(Enum):
    """Modes de simulation"""
    RANDOM = "random"              # Signaux aléatoires
    BULLISH = "bullish"            # Toujours bullish
    BEARISH = "bearish"            # Toujours bearish
    REALISTIC = "realistic"        # Simulation réaliste
    TREND_FOLLOWING = "trend"      # Suit une tendance


class SignalSimulator:
    """Simulateur de signaux AI"""
    
    def __init__(self, 
                 mode: str = "REALISTIC",
                 db_path: str = "db/simulated_signals.json"):
        """
        Initialise le simulateur
        
        Args:
            mode: Mode de simulation (RANDOM, BULLISH, BEARISH, REALISTIC, TREND_FOLLOWING)
            db_path: Chemin pour sauvegarder l'historique
        """
        try:
            self.mode = SimulationMode(mode.lower())
        except ValueError:
            print(f"⚠️ Mode invalide: {mode}, utilisation de REALISTIC")
            self.mode = SimulationMode.REALISTIC
        
        self.db_path = db_path
        self.history = []
        
        # État de la tendance (pour mode REALISTIC/TREND)
        self.current_trend = "neutral"  # bullish, bearish, neutral
        self.trend_strength = 0.5  # 0-1
        self.trend_duration = 0  # compteur
        
        # Charger historique
        self._load_history()
        
        print(f"🎯 Signal Simulator initialized - Mode: {self.mode.value}")
    
    def _load_history(self):
        """Charge l'historique des signaux"""
        try:
            if Path(self.db_path).exists():
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.history = data.get("signals", [])
                    self.current_trend = data.get("current_trend", "neutral")
                    self.trend_strength = data.get("trend_strength", 0.5)
        except Exception as e:
            print(f"⚠️ Erreur chargement historique: {e}")
    
    def _save_history(self):
        """Sauvegarde l'historique"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "signals": self.history[-100:],  # Garder 100 derniers
                "current_trend": self.current_trend,
                "trend_strength": self.trend_strength,
                "last_update": datetime.utcnow().isoformat()
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde historique: {e}")
    
    def generate_signal(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Génère un signal simulé
        
        Args:
            symbol: Paire de trading
        
        Returns:
            Signal avec bias, confidence, action, reasons
        """
        if self.mode == SimulationMode.RANDOM:
            return self._generate_random_signal(symbol)
        
        elif self.mode == SimulationMode.BULLISH:
            return self._generate_bullish_signal(symbol)
        
        elif self.mode == SimulationMode.BEARISH:
            return self._generate_bearish_signal(symbol)
        
        elif self.mode == SimulationMode.REALISTIC:
            return self._generate_realistic_signal(symbol)
        
        elif self.mode == SimulationMode.TREND_FOLLOWING:
            return self._generate_trend_signal(symbol)
        
        else:
            return self._generate_realistic_signal(symbol)
    
    def _generate_random_signal(self, symbol: str) -> Dict[str, Any]:
        """Signal aléatoire"""
        biases = ["bullish", "bearish", "neutral"]
        bias = random.choice(biases)
        confidence = round(random.uniform(0.5, 0.95), 2)
        
        if bias == "bullish":
            action = "BUY"
            reasons = [
                random.choice([
                    "Strong momentum detected",
                    "Volume spike",
                    "Price above MA",
                    "Bullish divergence",
                    "Support level held"
                ])
            ]
        elif bias == "bearish":
            action = "SELL"
            reasons = [
                random.choice([
                    "Weak momentum",
                    "Resistance rejected",
                    "Bearish divergence",
                    "Price below MA",
                    "Volume declining"
                ])
            ]
        else:
            action = "HOLD"
            reasons = ["No clear trend", "Wait for confirmation"]
        
        signal = {
            "symbol": symbol,
            "bias": bias,
            "confidence": confidence,
            "action": action,
            "reasons": reasons,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.mode.value
        }
        
        self._save_signal(signal)
        return signal
    
    def _generate_bullish_signal(self, symbol: str) -> Dict[str, Any]:
        """Toujours bullish"""
        confidence = round(random.uniform(0.7, 0.95), 2)
        
        reasons = [
            "Simulated LONG signal",
            "Strong bullish momentum",
            "Volume increasing"
        ]
        
        signal = {
            "symbol": symbol,
            "bias": "bullish",
            "confidence": confidence,
            "action": "BUY",
            "reasons": reasons,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.mode.value
        }
        
        self._save_signal(signal)
        return signal
    
    def _generate_bearish_signal(self, symbol: str) -> Dict[str, Any]:
        """Toujours bearish"""
        confidence = round(random.uniform(0.7, 0.95), 2)
        
        reasons = [
            "Simulated SHORT signal",
            "Strong bearish momentum",
            "Resistance rejected"
        ]
        
        signal = {
            "symbol": symbol,
            "bias": "bearish",
            "confidence": confidence,
            "action": "SELL",
            "reasons": reasons,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.mode.value
        }
        
        self._save_signal(signal)
        return signal
    
    def _generate_realistic_signal(self, symbol: str) -> Dict[str, Any]:
        """Signal réaliste avec tendances"""
        
        # Update trend si nécessaire
        self._update_trend()
        
        # Générer signal basé sur tendance actuelle
        if self.current_trend == "bullish":
            # 70% chance de signal bullish
            if random.random() < 0.7:
                bias = "bullish"
                action = "BUY"
                reasons = [
                    "Uptrend continuation",
                    "Higher highs detected",
                    f"Trend strength: {int(self.trend_strength * 100)}%"
                ]
            else:
                bias = "neutral"
                action = "HOLD"
                reasons = ["Consolidation phase", "Wait for breakout"]
        
        elif self.current_trend == "bearish":
            # 70% chance de signal bearish
            if random.random() < 0.7:
                bias = "bearish"
                action = "SELL"
                reasons = [
                    "Downtrend continuation",
                    "Lower lows detected",
                    f"Trend strength: {int(self.trend_strength * 100)}%"
                ]
            else:
                bias = "neutral"
                action = "HOLD"
                reasons = ["Consolidation phase", "Wait for confirmation"]
        
        else:  # neutral
            # Marché range
            choice = random.random()
            if choice < 0.3:
                bias = "bullish"
                action = "BUY"
                reasons = ["Support bounce", "Range low"]
            elif choice < 0.6:
                bias = "bearish"
                action = "SELL"
                reasons = ["Resistance rejection", "Range high"]
            else:
                bias = "neutral"
                action = "HOLD"
                reasons = ["Range market", "No clear direction"]
        
        # Confidence basée sur trend strength
        base_confidence = 0.5 + (self.trend_strength * 0.3)
        confidence = round(base_confidence + random.uniform(-0.1, 0.15), 2)
        confidence = max(0.5, min(0.95, confidence))
        
        signal = {
            "symbol": symbol,
            "bias": bias,
            "confidence": confidence,
            "action": action,
            "reasons": reasons,
            "trend": self.current_trend,
            "trend_strength": round(self.trend_strength, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.mode.value
        }
        
        self._save_signal(signal)
        return signal
    
    def _update_trend(self):
        """Update la tendance courante (pour mode REALISTIC)"""
        self.trend_duration += 1
        
        # Changer de tendance après 5-15 signaux
        if self.trend_duration > random.randint(5, 15):
            # Nouveau trend
            trends = ["bullish", "bearish", "neutral"]
            old_trend = self.current_trend
            
            # Éviter de répéter le même trend
            trends.remove(old_trend)
            self.current_trend = random.choice(trends)
            
            # Nouvelle strength
            self.trend_strength = round(random.uniform(0.4, 0.9), 2)
            
            # Reset duration
            self.trend_duration = 0
            
            print(f"📊 Trend change: {old_trend} → {self.current_trend} (strength: {self.trend_strength})")
        else:
            # Varier légèrement la strength
            self.trend_strength += random.uniform(-0.05, 0.05)
            self.trend_strength = max(0.3, min(0.95, self.trend_strength))
    
    def _generate_trend_signal(self, symbol: str) -> Dict[str, Any]:
        """Signal suivant une tendance forte"""
        # Similaire à realistic mais avec plus de persistance
        self.trend_duration += 1
        
        # Changer de tendance moins souvent (10-30 signaux)
        if self.trend_duration > random.randint(10, 30):
            trends = ["bullish", "bearish"]
            self.current_trend = random.choice(trends)
            self.trend_strength = round(random.uniform(0.7, 0.95), 2)
            self.trend_duration = 0
        
        if self.current_trend == "bullish":
            bias = "bullish"
            action = "BUY"
            reasons = [
                "Strong uptrend",
                "Momentum increasing",
                f"Trend confirmed for {self.trend_duration} signals"
            ]
        else:
            bias = "bearish"
            action = "SELL"
            reasons = [
                "Strong downtrend",
                "Momentum decreasing",
                f"Trend confirmed for {self.trend_duration} signals"
            ]
        
        confidence = round(0.75 + random.uniform(-0.1, 0.2), 2)
        
        signal = {
            "symbol": symbol,
            "bias": bias,
            "confidence": confidence,
            "action": action,
            "reasons": reasons,
            "trend": self.current_trend,
            "trend_strength": round(self.trend_strength, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.mode.value
        }
        
        self._save_signal(signal)
        return signal
    
    def _save_signal(self, signal: Dict[str, Any]):
        """Sauvegarde un signal dans l'historique"""
        self.history.append(signal)
        
        # Garder seulement les 100 derniers
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        # Sauvegarder sur disque
        self._save_history()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des signaux générés"""
        if not self.history:
            return {
                "total_signals": 0,
                "bullish": 0,
                "bearish": 0,
                "neutral": 0
            }
        
        bullish = sum(1 for s in self.history if s["bias"] == "bullish")
        bearish = sum(1 for s in self.history if s["bias"] == "bearish")
        neutral = sum(1 for s in self.history if s["bias"] == "neutral")
        
        avg_confidence = sum(s["confidence"] for s in self.history) / len(self.history)
        
        return {
            "total_signals": len(self.history),
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "bullish_percent": round((bullish / len(self.history)) * 100, 1),
            "bearish_percent": round((bearish / len(self.history)) * 100, 1),
            "neutral_percent": round((neutral / len(self.history)) * 100, 1),
            "avg_confidence": round(avg_confidence, 2),
            "current_trend": self.current_trend,
            "trend_strength": round(self.trend_strength, 2),
            "mode": self.mode.value
        }
    
    def set_mode(self, mode: str):
        """Change le mode de simulation"""
        try:
            self.mode = SimulationMode(mode.lower())
            print(f"✅ Mode changé: {self.mode.value}")
        except ValueError:
            print(f"❌ Mode invalide: {mode}")


# ========== API Helper Functions ==========

def get_simulator(mode: str = "REALISTIC") -> SignalSimulator:
    """Retourne une instance du simulateur"""
    return SignalSimulator(mode=mode)


if __name__ == "__main__":
    print("🎯 Testing Signal Simulator...\n")
    
    # Test tous les modes
    modes = ["RANDOM", "BULLISH", "BEARISH", "REALISTIC", "TREND_FOLLOWING"]
    
    for mode in modes:
        print(f"\n{'='*60}")
        print(f"Mode: {mode}")
        print('='*60)
        
        sim = SignalSimulator(mode=mode)
        
        # Générer 5 signaux
        for i in range(5):
            signal = sim.generate_signal("BTCUSDT")
            print(f"\nSignal #{i+1}:")
            print(f"  Bias: {signal['bias']}")
            print(f"  Action: {signal['action']}")
            print(f"  Confidence: {signal['confidence']}")
            print(f"  Reasons: {', '.join(signal['reasons'])}")
        
        # Stats
        print("\n📊 Statistics:")
        stats = sim.get_statistics()
        print(json.dumps(stats, indent=2))
    
    print("\n✅ Tests completed!")
