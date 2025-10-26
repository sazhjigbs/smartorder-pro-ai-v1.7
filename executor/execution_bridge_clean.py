#!/usr/bin/env python3
"""
⚡ SAFELOGIC SmartOrder PRO — Live Execution Bridge (Clean)
Connexion ExecutionAI → Signaux MTF Fusion → Positions Bybit
Phase 4 → Phase 5 transition finale
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class ExecutionBridge:
    def __init__(self):
        self.memory_file = "ai_core/ai_memory.json"
        self.execution_log = "logs/execution_bridge.log"
        self.min_confidence = 0.7
        self.max_position_size = 50  # USDT
        self.is_active = True
        
        os.makedirs("logs", exist_ok=True)
        os.makedirs("executor", exist_ok=True)
        
    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        try:
            with open(self.execution_log, "a", encoding="utf-8") as f:
                f.write(f"{log_entry}\n")
        except:
            pass
    
    def read_ai_signals(self) -> Dict[str, Any]:
        try:
            if Path(self.memory_file).exists():
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                return {
                    "confidence": memory.get("confidence", 0.0),
                    "bias": memory.get("bias", "neutral"),
                    "volatility": memory.get("volatility", 0.5),
                    "accuracy_rate": memory.get("accuracy_rate", 0.0)
                }
            return {"confidence": 0.0, "bias": "neutral", "volatility": 0.5, "accuracy_rate": 0.0}
        except:
            return {}
    
    def should_trade(self, signals: Dict[str, Any]) -> bool:
        if not signals:
            return False
        if signals["confidence"] < self.min_confidence:
            return False
        if signals["volatility"] > 0.9:
            self.log("Volatilite trop elevee")
            return False
        return True
    
    def simulate_execution(self, signals: Dict[str, Any]):
        if not self.should_trade(signals):
            return
            
        bias = signals["bias"]
        confidence = signals["confidence"]
        
        self.log(f"SIGNAL DETECTE: {bias} - Confiance: {confidence:.2%}")
        
        # Simulation d'execution
        if bias in ["bullish", "bearish"] and confidence > 0.7:
            position_size = self.max_position_size * confidence
            action = "LONG" if bias == "bullish" else "SHORT"
            
            self.log(f"SIMULATION: {action} BTCUSDT - Taille: {position_size:.1f} USDT")
            
            # Notifier (simulation)
            try:
                from tools.guardian_notify import notify_trading_alert
                notify_trading_alert("BTCUSDT", action.lower(), 67000, f"Sim: {position_size:.1f}")
            except:
                pass
    
    def run_bridge(self):
        self.log("Demarrage Execution Bridge")
        self.log(f"Confiance min: {self.min_confidence}")
        
        while self.is_active:
            try:
                signals = self.read_ai_signals()
                self.simulate_execution(signals)
            except Exception as e:
                self.log(f"Erreur: {str(e)}")
            
            time.sleep(30)  # Check every 30 seconds

def main():
    bridge = ExecutionBridge()
    
    try:
        bridge.run_bridge()
    except KeyboardInterrupt:
        bridge.log("Arret demande")
    except Exception as e:
        bridge.log(f"Erreur fatale: {str(e)}")

if __name__ == "__main__":
    main()