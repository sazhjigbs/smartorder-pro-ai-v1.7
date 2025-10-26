#!/usr/bin/env python3
"""
⚡ SAFELOGIC SmartOrder PRO — Live Execution Bridge
Connexion ExecutionAI → Signaux MTF Fusion → Positions Bybit réelles
Phase 4 → Phase 5 transition
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Import des modules locaux
try:
    from core.bybit_client import wallet_spot_balances, futures_positions, _post, _get
    from ai_core.ai_memory import load_memory, save_memory
except ImportError as e:
    print(f"⚠️ Import error: {e}")

class LiveExecutionBridge:
    """
    Bridge entre les signaux AI et l'exécution réelle
    """
    
    def __init__(self):
        self.memory_file = "ai_core/ai_memory.json"
        self.execution_log = "logs/execution_bridge.log"
        self.min_confidence = 0.6  # Seuil minimum pour exécuter
        self.max_position_size = 100  # USDT max par trade
        self.is_active = True
        self.last_execution = None
        
        # Créer dossiers nécessaires
        os.makedirs("logs", exist_ok=True)
        os.makedirs("executor", exist_ok=True)
        
    def log_execution(self, message: str):
        """Log des exécutions"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        print(log_entry.strip())
        
        try:
            with open(self.execution_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"❌ Erreur log: {str(e)}")
    
    def read_ai_signals(self) -> Dict[str, Any]:
        """Lit les signaux depuis la mémoire AI"""
        try:
            if Path(self.memory_file).exists():
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                    
                signals = {
                    "confidence": memory.get("confidence", 0.0),
                    "bias": memory.get("bias", "neutral"),
                    "volatility": memory.get("volatility", 0.5),
                    "last_update": memory.get("last_update"),
                    "accuracy_rate": memory.get("accuracy_rate", 0.0),
                    "learning_score": memory.get("learning_score", 0.0)
                }
                
                return signals
            else:
                return {
                    "confidence": 0.0,
                    "bias": "neutral", 
                    "volatility": 0.5,
                    "last_update": None,
                    "accuracy_rate": 0.0,
                    "learning_score": 0.0
                }
        except Exception as e:
            self.log_execution(f"❌ Erreur lecture signaux AI: {str(e)}")
            return {}\n    \n    def get_current_positions(self) -> Dict[str, Any]:\n        \"\"\"Récupère les positions actuelles\"\"\"\n        try:\n            # Positions futures\n            futures_data = futures_positions()\n            positions = {\n                \"futures\": futures_data.get(\"futures\", []),\n                \"total_unrealized_pnl\": 0.0,\n                \"position_count\": 0\n            }\n            \n            # Calculer PnL total\n            for pos in positions[\"futures\"]:\n                if pos.get(\"size\", \"0\") != \"0\":\n                    positions[\"position_count\"] += 1\n                    try:\n                        pnl = float(pos.get(\"unrealPnl\", 0))\n                        positions[\"total_unrealized_pnl\"] += pnl\n                    except:\n                        continue\n            \n            return positions\n            \n        except Exception as e:\n            self.log_execution(f\"❌ Erreur positions: {str(e)}\")\n            return {\"futures\": [], \"total_unrealized_pnl\": 0.0, \"position_count\": 0}\n    \n    def should_execute_signal(self, signals: Dict[str, Any], positions: Dict[str, Any]) -> bool:\n        \"\"\"Détermine si un signal doit être exécuté\"\"\"\n        \n        # Vérifications de base\n        if not signals or signals[\"confidence\"] < self.min_confidence:\n            return False\n            \n        # Pas d'exécution si trop de positions ouvertes\n        if positions[\"position_count\"] > 3:\n            self.log_execution(\"⚠️ Trop de positions ouvertes, pas d'exécution\")\n            return False\n            \n        # Pas d'exécution si PnL très négatif\n        if positions[\"total_unrealized_pnl\"] < -50:  # -50 USDT\n            self.log_execution(\"⚠️ PnL trop négatif, pas d'exécution\")\n            return False\n            \n        # Pas d'exécution si volatilité trop élevée\n        if signals[\"volatility\"] > 0.9:\n            self.log_execution(\"⚠️ Volatilité trop élevée, pas d'exécution\")\n            return False\n            \n        # Éviter les exécutions trop rapprochées\n        if self.last_execution:\n            time_diff = (datetime.now() - self.last_execution).total_seconds()\n            if time_diff < 300:  # 5 minutes minimum\n                return False\n        \n        return True\n    \n    def calculate_position_size(self, signals: Dict[str, Any]) -> float:\n        \"\"\"Calcule la taille de position basée sur la confiance\"\"\"\n        base_size = 20.0  # USDT de base\n        \n        # Ajuster selon la confiance\n        confidence_multiplier = signals[\"confidence\"]\n        \n        # Réduire selon la volatilité\n        volatility_reducer = 1.0 - (signals[\"volatility\"] * 0.5)\n        \n        # Ajuster selon le learning score\n        learning_bonus = 1.0 + (signals.get(\"learning_score\", 0) / 200)\n        \n        position_size = base_size * confidence_multiplier * volatility_reducer * learning_bonus\n        \n        # Limiter à la taille max\n        return min(position_size, self.max_position_size)\n    \n    def execute_market_order(self, symbol: str, side: str, qty: float) -> bool:\n        \"\"\"Exécute un ordre de marché\"\"\"\n        try:\n            # Convertir la quantité USDT en quantité de crypto\n            # Pour BTCUSDT, si on veut trader 20 USDT à 67000 USD, qty = 20/67000 = 0.0002985 BTC\n            \n            # Récupérer le prix actuel (approximatif)\n            current_price = 67000.0  # Placeholder - devrait venir de l'API\n            \n            if \"USDT\" in symbol:\n                # Pour les paires USDT, calculer la quantité en crypto\n                crypto_qty = qty / current_price\n                qty_formatted = f\"{crypto_qty:.6f}\"\n            else:\n                qty_formatted = f\"{qty:.6f}\"\n            \n            order_data = {\n                \"category\": \"linear\",  # Futures\n                \"symbol\": symbol,\n                \"side\": side.capitalize(),\n                \"orderType\": \"Market\",\n                \"qty\": qty_formatted,\n                \"timeInForce\": \"IOC\"\n            }\n            \n            self.log_execution(f\"📤 Tentative ordre: {side} {qty_formatted} {symbol}\")\n            \n            # Exécuter l'ordre via l'API Bybit\n            success, response = _post(\"/v5/order/create\", order_data)\n            \n            if success:\n                order_id = response.get(\"result\", {}).get(\"orderId\", \"unknown\")\n                self.log_execution(f\"✅ Ordre exécuté: {order_id}\")\n                self.last_execution = datetime.now()\n                return True\n            else:\n                self.log_execution(f\"❌ Échec ordre: {response}\")\n                return False\n                \n        except Exception as e:\n            self.log_execution(f\"💥 Erreur exécution: {str(e)}\")\n            return False\n    \n    def process_signals(self):\n        \"\"\"Traite les signaux AI et exécute si nécessaire\"\"\"\n        try:\n            # 1. Lire les signaux AI\n            signals = self.read_ai_signals()\n            if not signals:\n                return\n            \n            # 2. Récupérer les positions actuelles\n            positions = self.get_current_positions()\n            \n            # 3. Décider si exécuter\n            if not self.should_execute_signal(signals, positions):\n                return\n            \n            # 4. Déterminer l'action basée sur le biais\n            bias = signals[\"bias\"]\n            confidence = signals[\"confidence\"]\n            \n            self.log_execution(f\"🧠 Signal détecté: {bias} (conf: {confidence:.2%})\")\n            \n            # 5. Calculer la taille de position\n            position_size = self.calculate_position_size(signals)\n            \n            # 6. Déterminer le symbole (pour l'instant BTCUSDT)\n            symbol = \"BTCUSDT\"\n            \n            # 7. Exécuter selon le biais\n            if bias == \"bullish\" and confidence > 0.7:\n                success = self.execute_market_order(symbol, \"Buy\", position_size)\n                if success:\n                    self.log_execution(f\"🚀 Position LONG ouverte: {position_size} USDT\")\n                    \n            elif bias == \"bearish\" and confidence > 0.7:\n                success = self.execute_market_order(symbol, \"Sell\", position_size)\n                if success:\n                    self.log_execution(f\"📉 Position SHORT ouverte: {position_size} USDT\")\n                    \n            # 8. Notifier via Telegram\n            try:\n                from tools.guardian_notify import notify_trading_alert\n                notify_trading_alert(\n                    symbol, \n                    bias, \n                    67000,  # Prix approximatif\n                    f\"Size: {position_size} USDT\"\n                )\n            except:\n                pass  # Pas grave si notification échoue\n                \n        except Exception as e:\n            self.log_execution(f\"💥 Erreur process_signals: {str(e)}\")\n    \n    def run_continuous_bridge(self):\n        \"\"\"Lance le bridge en continu\"\"\"\n        self.log_execution(\"🚀 Démarrage Live Execution Bridge\")\n        self.log_execution(f\"🎯 Confiance min: {self.min_confidence}\")\n        self.log_execution(f\"💰 Taille max: {self.max_position_size} USDT\")\n        \n        while self.is_active:\n            try:\n                self.process_signals()\n            except Exception as e:\n                self.log_execution(f\"💥 Erreur bridge: {str(e)}\")\n            \n            # Attendre 30 secondes avant le prochain cycle\n            time.sleep(30)\n    \n    def stop_bridge(self):\n        \"\"\"Arrête le bridge\"\"\"\n        self.is_active = False\n        self.log_execution(\"🛑 Live Execution Bridge arrêté\")\n\ndef main():\n    \"\"\"Point d'entrée principal\"\"\"\n    bridge = LiveExecutionBridge()\n    \n    try:\n        bridge.run_continuous_bridge()\n    except KeyboardInterrupt:\n        bridge.stop_bridge()\n        print(\"\\n👋 Arrêt demandé par l'utilisateur\")\n    except Exception as e:\n        bridge.log_execution(f\"💥 Erreur fatale: {str(e)}\")\n\nif __name__ == \"__main__\":\n    main()