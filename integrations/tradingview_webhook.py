"""
TradingView Webhook Integration
Reçoit et traite les signaux de TradingView
"""
from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import time
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SignalAction(Enum):
    BUY = "buy"
    SELL = "sell"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"


@dataclass
class TradingViewSignal:
    """Signal reçu de TradingView"""
    symbol: str
    action: SignalAction
    price: Optional[float] = None
    quantity: Optional[float] = None
    strategy: Optional[str] = None
    timeframe: Optional[str] = None
    timestamp: float = 0.0
    metadata: Dict = None


class TradingViewWebhook:
    """Gestionnaire de webhooks TradingView"""
    
    def __init__(self, secret_key: Optional[str] = None, port: int = 5000):
        self.app = Flask(__name__)
        self.secret_key = secret_key
        self.port = port
        self.signal_handlers: Dict[str, Callable] = {}
        self.signal_log: list = []
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Configure les routes Flask"""
        
        @self.app.route('/webhook/tradingview', methods=['POST'])
        def webhook():
            try:
                # Vérification de sécurité
                if not self._verify_signature(request):
                    return jsonify({"error": "Invalid signature"}), 403
                
                # Parse le signal
                data = request.get_json()
                signal = self._parse_signal(data)
                
                if not signal:
                    return jsonify({"error": "Invalid signal format"}), 400
                
                # Enregistrer le signal
                self.signal_log.append({
                    "signal": signal,
                    "timestamp": time.time(),
                    "raw_data": data
                })
                
                # Exécuter les handlers
                results = self._execute_handlers(signal)
                
                return jsonify({
                    "status": "success",
                    "signal": {
                        "symbol": signal.symbol,
                        "action": signal.action.value,
                        "price": signal.price
                    },
                    "handlers_executed": len(results),
                    "results": results
                }), 200
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/webhook/test', methods=['GET'])
        def test():
            return jsonify({
                "status": "active",
                "signals_received": len(self.signal_log),
                "registered_handlers": list(self.signal_handlers.keys())
            })
    
    def _verify_signature(self, request) -> bool:
        """Vérifie la signature HMAC du webhook"""
        if not self.secret_key:
            return True  # Pas de vérification si pas de clé
        
        signature = request.headers.get('X-TradingView-Signature')
        if not signature:
            return False
        
        body = request.get_data()
        expected_sig = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_sig)
    
    def _parse_signal(self, data: Dict) -> Optional[TradingViewSignal]:
        """Parse les données du webhook"""
        try:
            # Format standard TradingView
            # {"symbol": "BTCUSDT", "action": "buy", "price": 50000, "strategy": "RSI_MA"}
            
            symbol = data.get('symbol') or data.get('ticker')
            action_str = data.get('action') or data.get('order')
            
            if not symbol or not action_str:
                return None
            
            # Normaliser l'action
            action_map = {
                'buy': SignalAction.BUY,
                'sell': SignalAction.SELL,
                'long': SignalAction.BUY,
                'short': SignalAction.SELL,
                'close': SignalAction.CLOSE_LONG,
                'exit': SignalAction.CLOSE_LONG
            }
            
            action = action_map.get(action_str.lower(), SignalAction.BUY)
            
            signal = TradingViewSignal(
                symbol=symbol.upper(),
                action=action,
                price=data.get('price'),
                quantity=data.get('quantity') or data.get('contracts'),
                strategy=data.get('strategy'),
                timeframe=data.get('timeframe') or data.get('interval'),
                timestamp=time.time(),
                metadata=data
            )
            
            return signal
            
        except Exception as e:
            print(f"Error parsing signal: {e}")
            return None
    
    def register_handler(self, name: str, handler: Callable):
        """
        Enregistre un handler pour traiter les signaux
        
        handler doit accepter un TradingViewSignal et retourner un Dict
        """
        self.signal_handlers[name] = handler
    
    def _execute_handlers(self, signal: TradingViewSignal) -> list:
        """Exécute tous les handlers enregistrés"""
        results = []
        
        for name, handler in self.signal_handlers.items():
            try:
                result = handler(signal)
                results.append({
                    "handler": name,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "handler": name,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def run(self, debug: bool = False):
        """Lance le serveur webhook"""
        print(f"🚀 TradingView Webhook Server starting on port {self.port}")
        print(f"📡 Endpoint: http://localhost:{self.port}/webhook/tradingview")
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)
    
    def get_signal_history(self, limit: int = 50) -> list:
        """Retourne l'historique des signaux"""
        return self.signal_log[-limit:]
    
    def get_statistics(self) -> Dict:
        """Statistiques des signaux reçus"""
        if not self.signal_log:
            return {
                "total_signals": 0,
                "by_action": {},
                "by_symbol": {}
            }
        
        by_action = {}
        by_symbol = {}
        
        for entry in self.signal_log:
            signal = entry['signal']
            
            action = signal.action.value
            by_action[action] = by_action.get(action, 0) + 1
            
            symbol = signal.symbol
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
        
        return {
            "total_signals": len(self.signal_log),
            "by_action": by_action,
            "by_symbol": by_symbol,
            "first_signal": self.signal_log[0]['timestamp'] if self.signal_log else None,
            "last_signal": self.signal_log[-1]['timestamp'] if self.signal_log else None
        }


# Exemple de création d'un handler personnalisé
def example_trading_handler(signal: TradingViewSignal) -> Dict:
    """Handler exemple qui simule un trade"""
    print(f"📊 Signal reçu: {signal.action.value} {signal.symbol} @ {signal.price}")
    
    # Ici, vous intégreriez votre logique de trading
    # Par exemple, appeler votre SmartOrderEngine
    
    return {
        "executed": True,
        "symbol": signal.symbol,
        "action": signal.action.value,
        "price": signal.price
    }


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer le webhook avec secret pour sécurité
    webhook = TradingViewWebhook(
        secret_key="your_secret_key_here",  # À changer
        port=5000
    )
    
    # Enregistrer des handlers
    webhook.register_handler("trading", example_trading_handler)
    
    # Lancer le serveur
    webhook.run(debug=True)
    
    # Pour tester:
    # curl -X POST http://localhost:5000/webhook/tradingview \
    #   -H "Content-Type: application/json" \
    #   -d '{"symbol":"BTCUSDT","action":"buy","price":50000,"strategy":"MA_Crossover"}'
