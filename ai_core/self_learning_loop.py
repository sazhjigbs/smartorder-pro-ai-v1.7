#!/usr/bin/env python3
"""
🧠 SAFELOGIC SmartOrder PRO — Phase 5: Self-Learning Loop
Boucle autonome d'apprentissage : logs → AI Learner → Memory → ExecutionAI
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class SelfLearningLoop:
    """
    Classe principale pour la boucle d'apprentissage autonome Phase 5
    """
    
    def __init__(self):
        self.db_path = "ai_core/learning_memory.db"
        self.memory_file = "ai_core/ai_memory.json" 
        self.learning_interval = 60  # 1 minute
        self.adaptation_threshold = 0.7  # Seuil pour déclencher adaptation
        self.init_database()
        
    def init_database(self):
        """Initialise la base SQLite pour l'apprentissage"""
        os.makedirs("ai_core", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    signals_analyzed INTEGER,
                    accuracy_score REAL,
                    adaptation_made BOOLEAN,
                    market_context TEXT,
                    performance_delta REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_patterns (
                    id INTEGER PRIMARY KEY,
                    pattern_name TEXT UNIQUE,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.5,
                    last_seen TEXT,
                    adaptations INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_feedback (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    signal_type TEXT,
                    expected_outcome TEXT,
                    actual_outcome TEXT,
                    profit_loss REAL,
                    market_volatility REAL,
                    learning_weight REAL
                )
            """)
    
    def analyze_recent_performance(self) -> Dict[str, Any]:
        """Analyse les performances récentes depuis les logs"""
        performance = {
            "total_signals": 0,
            "successful_signals": 0,
            "failed_signals": 0,
            "accuracy_rate": 0.0,
            "avg_confidence": 0.0,
            "market_bias": "neutral",
            "volatility_score": 0.0
        }
        
        try:
            # Analyser les logs récents (dernière heure)
            recent_logs = self._collect_recent_logs()
            
            for log_entry in recent_logs:
                if "signal" in log_entry.lower():
                    performance["total_signals"] += 1
                    
                    # Déterminer si le signal était réussi
                    if any(word in log_entry.lower() for word in ["success", "profit", "win"]):
                        performance["successful_signals"] += 1
                    elif any(word in log_entry.lower() for word in ["loss", "fail", "error"]):
                        performance["failed_signals"] += 1
            
            # Calculer le taux de précision
            if performance["total_signals"] > 0:
                performance["accuracy_rate"] = performance["successful_signals"] / performance["total_signals"]
            
            # Lire la mémoire AI existante
            if Path(self.memory_file).exists():
                with open(self.memory_file, 'r') as f:
                    memory_data = json.load(f)
                    performance["avg_confidence"] = memory_data.get("confidence", 0.5)
                    performance["market_bias"] = memory_data.get("bias", "neutral")
                    performance["volatility_score"] = memory_data.get("volatility", 0.5)
            
        except Exception as e:
            print(f"⚠️ Erreur analyse performance: {str(e)}")
        
        return performance
    
    def _collect_recent_logs(self) -> List[str]:
        """Collecte les logs récents pour analyse"""
        logs = []
        log_patterns = ["*.log", "ai_*.log", "execution_*.log"]
        
        for pattern in log_patterns:
            try:
                log_files = Path(".").glob(pattern)
                for log_file in log_files:
                    if log_file.exists():
                        # Lire seulement les dernières lignes (plus récent)
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            # Prendre les 50 dernières lignes
                            recent_lines = lines[-50:] if len(lines) > 50 else lines
                            logs.extend(recent_lines)
            except:
                continue
        
        return logs
    
    def detect_market_patterns(self, performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Détecte les patterns de marché récurrents"""
        patterns = []
        
        # Pattern 1: Tendance haussière forte
        if performance["market_bias"] == "bullish" and performance["volatility_score"] > 0.7:
            patterns.append({
                "name": "strong_bullish_trend",
                "confidence": performance["avg_confidence"] * 1.1,
                "action": "increase_long_bias"
            })
        
        # Pattern 2: Marché range avec volatilité faible  
        elif performance["volatility_score"] < 0.3 and performance["accuracy_rate"] < 0.5:
            patterns.append({
                "name": "low_volatility_range",
                "confidence": performance["avg_confidence"] * 0.8,
                "action": "reduce_position_size"
            })
        
        # Pattern 3: Haute volatilité avec signaux contradictoires
        elif performance["volatility_score"] > 0.8 and performance["accuracy_rate"] < 0.4:
            patterns.append({
                "name": "high_volatility_chaos", 
                "confidence": 0.3,
                "action": "pause_trading"
            })
        
        # Pattern 4: Performance constante
        elif performance["accuracy_rate"] > 0.7:
            patterns.append({
                "name": "consistent_performance",
                "confidence": performance["avg_confidence"] * 1.2,
                "action": "increase_confidence"
            })
        
        return patterns
    
    def update_memory_with_learning(self, performance: Dict[str, Any], patterns: List[Dict[str, Any]]):
        """Met à jour la mémoire AI avec les apprentissages"""
        try:
            # Charger la mémoire existante
            if Path(self.memory_file).exists():
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
            else:
                memory = {
                    "confidence": 0.5,
                    "bias": "neutral",
                    "volatility": 0.5,
                    "learning_score": 0.0,
                    "adaptations": 0,
                    "last_update": None
                }
            
            # Appliquer les apprentissages
            for pattern in patterns:
                if pattern["action"] == "increase_long_bias":
                    memory["bias"] = "bullish"
                    memory["confidence"] = min(1.0, pattern["confidence"])
                    
                elif pattern["action"] == "reduce_position_size":
                    memory["confidence"] = max(0.2, memory["confidence"] * 0.8)
                    
                elif pattern["action"] == "pause_trading":
                    memory["confidence"] = 0.1
                    memory["bias"] = "neutral"
                    
                elif pattern["action"] == "increase_confidence":
                    memory["confidence"] = min(1.0, pattern["confidence"])
                    memory["learning_score"] = min(100, memory.get("learning_score", 0) + 5)
            
            # Mise à jour générale
            memory["volatility"] = performance["volatility_score"]
            memory["adaptations"] = memory.get("adaptations", 0) + len(patterns)
            memory["last_update"] = datetime.now().isoformat()
            memory["accuracy_rate"] = performance["accuracy_rate"]
            
            # Sauvegarder
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
            
            print(f"🧠 Mémoire mise à jour: {len(patterns)} adaptations")
            
        except Exception as e:
            print(f"❌ Erreur mise à jour mémoire: {str(e)}")
    
    def log_learning_session(self, performance: Dict[str, Any], patterns: List[Dict[str, Any]]):
        """Enregistre la session d'apprentissage dans la DB"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO learning_sessions 
                    (timestamp, signals_analyzed, accuracy_score, adaptation_made, market_context, performance_delta)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    performance["total_signals"],
                    performance["accuracy_rate"],
                    len(patterns) > 0,
                    performance["market_bias"],
                    performance["accuracy_rate"] - 0.5  # Delta par rapport à la baseline
                ))
                
            # Enregistrer les patterns détectés
            for pattern in patterns:
                conn.execute("""
                    INSERT OR REPLACE INTO market_patterns 
                    (pattern_name, success_count, confidence, last_seen, adaptations)
                    VALUES (?, 
                            COALESCE((SELECT success_count FROM market_patterns WHERE pattern_name = ?), 0) + 1,
                            ?, ?, 
                            COALESCE((SELECT adaptations FROM market_patterns WHERE pattern_name = ?), 0) + 1)
                """, (
                    pattern["name"], pattern["name"],
                    pattern["confidence"], 
                    datetime.now().isoformat(),
                    pattern["name"]
                ))
                
        except Exception as e:
            print(f"❌ Erreur log session: {str(e)}")
    
    def learning_cycle(self):
        """Cycle complet d'apprentissage"""
        print("🔄 Début cycle d'apprentissage Phase 5...")
        
        # 1. Analyser les performances récentes
        performance = self.analyze_recent_performance()
        print(f"📊 Signaux analysés: {performance['total_signals']}, Précision: {performance['accuracy_rate']:.2%}")
        
        # 2. Détecter les patterns de marché
        patterns = self.detect_market_patterns(performance)
        print(f"🔍 Patterns détectés: {len(patterns)}")
        
        # 3. Décider s'il faut adapter
        adaptation_needed = (
            performance["accuracy_rate"] < self.adaptation_threshold or
            performance["volatility_score"] > 0.8 or
            len(patterns) > 0
        )
        
        if adaptation_needed:
            print("🧠 Adaptation nécessaire - Mise à jour de la mémoire...")
            
            # 4. Mettre à jour la mémoire AI
            self.update_memory_with_learning(performance, patterns)
            
            # 5. Logger la session
            self.log_learning_session(performance, patterns)
            
            # 6. Notifier via Telegram si disponible
            try:
                from tools.guardian_notify import notify_ai_status
                notify_ai_status(
                    "Phase 5 Learning",
                    int(performance["accuracy_rate"] * 100),
                    performance["market_bias"]
                )
            except:
                pass  # Pas grave si notification échoue
                
        else:
            print("✅ Performance stable - Pas d'adaptation requise")
        
        print("🔄 Cycle d'apprentissage terminé\n")
    
    def run_continuous_learning(self):
        """Lance la boucle d'apprentissage continue"""
        print("🚀 Démarrage Self-Learning Loop Phase 5")
        print(f"⏱️ Intervalle: {self.learning_interval}s")
        print(f"🎯 Seuil d'adaptation: {self.adaptation_threshold}")
        
        while True:
            try:
                self.learning_cycle()
            except Exception as e:
                print(f"💥 Erreur dans le cycle d'apprentissage: {str(e)}")
            
            # Attendre avant le prochain cycle
            time.sleep(self.learning_interval)

def main():
    """Point d'entrée principal"""
    learner = SelfLearningLoop()
    learner.run_continuous_learning()

if __name__ == "__main__":
    main()