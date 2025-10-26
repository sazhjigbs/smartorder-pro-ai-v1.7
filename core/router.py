import os
import time
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("router")

# Configuration from .env
EXCH_EXEC = os.getenv("EXCH_EXEC", "bybit,binance,kucoin").split(",")
EXCH_READ = os.getenv("EXCH_READ", "bybit,binance,kucoin").split(",")
ACTIVE_EXCHANGE = os.getenv("ACTIVE_EXCHANGE", "bybit")

# Thresholds for aiguillage rules
SPREAD_THRESHOLD = float(os.getenv("SPREAD_THRESHOLD", "0.1"))  # 0.1%
LATENCY_THRESHOLD = float(os.getenv("LATENCY_THRESHOLD", "500"))  # 500ms
MIN_BALANCE_USDT = float(os.getenv("MIN_BALANCE_USDT", "20"))  # 20 USDT

class MultiExchangeRouter:
    def __init__(self):
        self.last_route_log = {}
        
    def check_balance_sufficient(self, exchange: str, required_usdt: float) -> bool:
        """Règle 1: Vérifier solde suffisant"""
        try:
            # Mock balance check (in production, would query real API)
            mock_balances = {
                "bybit": 150.0,
                "binance": 80.0, 
                "kucoin": 200.0
            }
            
            balance = mock_balances.get(exchange, 0)
            is_sufficient = balance >= required_usdt
            
            logger.info(f"Balance check {exchange}: {balance} USDT >= {required_usdt} USDT = {is_sufficient}")
            return is_sufficient
            
        except Exception as e:
            logger.error(f"Balance check failed for {exchange}: {str(e)}")
            return False
    
    def check_spread_acceptable(self, exchange: str, symbol: str) -> Tuple[bool, float]:
        """Règle 2: Vérifier spread < seuil"""
        try:
            # Mock spread check (in production, would get real bid/ask)
            mock_spreads = {
                "bybit": {"BTCUSDT": 0.05, "ETHUSDT": 0.08},
                "binance": {"BTCUSDT": 0.03, "ETHUSDT": 0.06},
                "kucoin": {"BTCUSDT": 0.12, "ETHUSDT": 0.15}
            }
            
            spread = mock_spreads.get(exchange, {}).get(symbol, 0.2)
            is_acceptable = spread <= SPREAD_THRESHOLD
            
            logger.info(f"Spread check {exchange} {symbol}: {spread}% <= {SPREAD_THRESHOLD}% = {is_acceptable}")
            return is_acceptable, spread
            
        except Exception as e:
            logger.error(f"Spread check failed for {exchange}: {str(e)}")
            return False, 999.0
    
    def check_latency_acceptable(self, exchange: str) -> Tuple[bool, float]:
        """Règle 3: Vérifier latence < seuil"""
        try:
            start_time = time.time()
            
            # Mock latency test (in production, would ping real API)
            mock_latencies = {
                "bybit": 120,
                "binance": 80,
                "kucoin": 200
            }
            
            latency_ms = mock_latencies.get(exchange, 1000)
            is_acceptable = latency_ms <= LATENCY_THRESHOLD
            
            logger.info(f"Latency check {exchange}: {latency_ms}ms <= {LATENCY_THRESHOLD}ms = {is_acceptable}")
            return is_acceptable, latency_ms
            
        except Exception as e:
            logger.error(f"Latency check failed for {exchange}: {str(e)}")
            return False, 9999.0
    
    def check_min_notional_ok(self, exchange: str, symbol: str, quantity: float, price: float) -> bool:
        """Règle 4: Vérifier minNotional OK"""
        try:
            from core.fees_limits import get_symbol_constraints
            
            constraints = get_symbol_constraints(exchange, symbol)
            min_notional = constraints.get('minNotional', 10)
            
            notional_value = quantity * price
            is_ok = notional_value >= min_notional
            
            logger.info(f"MinNotional check {exchange} {symbol}: {notional_value} >= {min_notional} = {is_ok}")
            return is_ok
            
        except Exception as e:
            logger.error(f"MinNotional check failed for {exchange}: {str(e)}")
            return False
    
    def choose_exchange_with_aiguillage(self, symbol: str = "BTCUSDT", quantity: float = 0.001, 
                                      price: float = 67000, required_usdt: float = 20) -> str:
        """Règles d'aiguillage complètes (1-4)"""
        
        logger.info(f"=== AIGUILLAGE MULTI-EXCHANGE pour {symbol} ===")
        
        for exchange in EXCH_EXEC:
            logger.info(f"🔍 Testing {exchange}...")
            
            # Règle 1: Solde suffisant
            if not self.check_balance_sufficient(exchange, required_usdt):
                logger.warning(f"❌ {exchange} - Solde insuffisant")
                continue
            
            # Règle 2: MinNotional OK  
            if not self.check_min_notional_ok(exchange, symbol, quantity, price):
                logger.warning(f"❌ {exchange} - MinNotional non respecté")
                continue
                
            # Règle 3: Spread acceptable
            spread_ok, spread_value = self.check_spread_acceptable(exchange, symbol)
            if not spread_ok:
                logger.warning(f"❌ {exchange} - Spread trop élevé: {spread_value}%")
                continue
            
            # Règle 4: Latence acceptable
            latency_ok, latency_ms = self.check_latency_acceptable(exchange)
            if not latency_ok:
                logger.warning(f"❌ {exchange} - Latence trop élevée: {latency_ms}ms")
                continue
            
            # Toutes les règles OK
            logger.info(f"✅ {exchange} - Toutes les règles respectées!")
            self.log_route_decision(exchange, symbol, {
                "spread": spread_value,
                "latency": latency_ms,
                "reason": "aiguillage_success"
            })
            return exchange
        
        # Aucun exchange valide -> fallback sur ACTIVE_EXCHANGE
        logger.warning(f"⚠️ Aucun exchange valide, fallback sur {ACTIVE_EXCHANGE}")
        self.log_route_decision(ACTIVE_EXCHANGE, symbol, {"reason": "fallback"})
        return ACTIVE_EXCHANGE
    
    def log_route_decision(self, exchange: str, symbol: str, metadata: Dict):
        """Log la décision de routage pour transparence"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "route": exchange,
            "symbol": symbol,
            "metadata": metadata
        }
        
        # Save to state.json or log file
        try:
            import json
            with open("state.json", "r+") as f:
                state = json.load(f)
                if "routing_history" not in state:
                    state["routing_history"] = []
                
                state["routing_history"].append(log_entry)
                # Keep only last 10 entries
                state["routing_history"] = state["routing_history"][-10:]
                
                f.seek(0)
                json.dump(state, f, indent=2)
                f.truncate()
                
        except Exception as e:
            logger.error(f"Failed to log route decision: {str(e)}")

# Global router instance
router = MultiExchangeRouter()

def choose_exchange(symbol: str = "BTCUSDT", quantity: float = 0.001, price: float = 67000) -> str:
    """Choose exchange using aiguillage rules"""
    return router.choose_exchange_with_aiguillage(symbol, quantity, price)

def get_routing_history() -> List[Dict]:
    """Get recent routing decisions"""
    try:
        import json
        with open("state.json", "r") as f:
            state = json.load(f)
            return state.get("routing_history", [])
    except:
        return []
