#!/usr/bin/env python3
"""
UPDATE: CCXT Integration Module v2.1
Date: 2025-10-31
Description: Integration CCXT pour connexion exchanges reels
"""

import ccxt
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CCXTManager:
    """Gestionnaire de connexions CCXT"""
    
    def __init__(self, config_path: str = "/opt/smartorder-pro/config"):
        self.config_path = Path(config_path)
        self.exchanges = {}
        self.testnet = True  # Mode testnet par defaut
        
    def load_exchange_config(self) -> Dict:
        """Charge la configuration des exchanges"""
        try:
            with open(self.config_path / "exchanges.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement config exchanges: {e}")
            return {}
    
    def connect_exchange(self, exchange_name: str, credentials: Dict) -> bool:
        """Connecte un exchange via CCXT"""
        try:
            exchange_name_lower = exchange_name.lower()
            
            if exchange_name_lower == "bybit":
                exchange = ccxt.bybit({
                    'apiKey': credentials.get('api_key', ''),
                    'secret': credentials.get('secret', ''),
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                })
            elif exchange_name_lower == "binance":
                exchange = ccxt.binance({
                    'apiKey': credentials.get('api_key', ''),
                    'secret': credentials.get('secret', ''),
                    'enableRateLimit': True
                })
            elif exchange_name_lower == "okx":
                exchange = ccxt.okx({
                    'apiKey': credentials.get('api_key', ''),
                    'secret': credentials.get('secret', ''),
                    'password': credentials.get('password', ''),
                    'enableRateLimit': True
                })
            elif exchange_name_lower == "kucoin":
                exchange = ccxt.kucoin({
                    'apiKey': credentials.get('api_key', ''),
                    'secret': credentials.get('secret', ''),
                    'password': credentials.get('password', ''),
                    'enableRateLimit': True
                })
            else:
                logger.warning(f"Exchange {exchange_name} non supporte")
                return False
            
            # Test connexion
            if self.testnet or not credentials.get('api_key'):
                exchange.set_sandbox_mode(True)
            
            self.exchanges[exchange_name] = exchange
            logger.info(f"Exchange {exchange_name} connecte (testnet={self.testnet})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur connexion {exchange_name}: {e}")
            return False
    
    def get_ticker(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """Recupere le ticker d'un symbole"""
        try:
            if exchange_name not in self.exchanges:
                logger.warning(f"Exchange {exchange_name} non connecte")
                return None
            
            exchange = self.exchanges[exchange_name]
            ticker = exchange.fetch_ticker(symbol)
            
            return {
                "symbol": symbol,
                "last": ticker.get('last'),
                "bid": ticker.get('bid'),
                "ask": ticker.get('ask'),
                "volume": ticker.get('volume'),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur get_ticker {symbol} sur {exchange_name}: {e}")
            return None
    
    def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List]:
        """Recupere les bougies OHLCV"""
        try:
            if exchange_name not in self.exchanges:
                return None
            
            exchange = self.exchanges[exchange_name]
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            return ohlcv
        except Exception as e:
            logger.error(f"Erreur get_ohlcv {symbol}: {e}")
            return None
    
    def get_balance(self, exchange_name: str) -> Optional[Dict]:
        """Recupere le solde"""
        try:
            if exchange_name not in self.exchanges:
                return None
            
            exchange = self.exchanges[exchange_name]
            balance = exchange.fetch_balance()
            
            return {
                "total": balance.get('total', {}),
                "free": balance.get('free', {}),
                "used": balance.get('used', {})
            }
        except Exception as e:
            logger.error(f"Erreur get_balance {exchange_name}: {e}")
            return None
    
    def place_order(self, exchange_name: str, symbol: str, side: str, amount: float, 
                   price: Optional[float] = None, order_type: str = 'market') -> Optional[Dict]:
        """Place un ordre"""
        try:
            if exchange_name not in self.exchanges:
                return None
            
            exchange = self.exchanges[exchange_name]
            
            if order_type == 'market':
                order = exchange.create_market_order(symbol, side.lower(), amount)
            else:
                order = exchange.create_limit_order(symbol, side.lower(), amount, price)
            
            logger.info(f"Ordre place: {side} {amount} {symbol} @ {price or 'market'}")
            return order
            
        except Exception as e:
            logger.error(f"Erreur place_order: {e}")
            return None
    
    def cancel_order(self, exchange_name: str, order_id: str, symbol: str) -> bool:
        """Annule un ordre"""
        try:
            if exchange_name not in self.exchanges:
                return False
            
            exchange = self.exchanges[exchange_name]
            exchange.cancel_order(order_id, symbol)
            logger.info(f"Ordre {order_id} annule")
            return True
            
        except Exception as e:
            logger.error(f"Erreur cancel_order: {e}")
            return False

# Test du module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== CCXT INTEGRATION TEST ===")
    
    manager = CCXTManager()
    
    # Test connexion Bybit (testnet)
    success = manager.connect_exchange("bybit", {
        "api_key": "",
        "secret": ""
    })
    
    print(f"Connexion Bybit testnet: {success}")
    
    if success:
        # Test ticker
        ticker = manager.get_ticker("bybit", "BTC/USDT")
        if ticker:
            print(f"BTC/USDT ticker: ${ticker['last']:.2f}")
        
        # Test OHLCV
        ohlcv = manager.get_ohlcv("bybit", "BTC/USDT", "1h", 10)
        if ohlcv:
            print(f"OHLCV count: {len(ohlcv)} bougies")
            print(f"Dernier prix: ${ohlcv[-1][4]:.2f}")
    
    print("\nNote: Mode testnet actif - aucun ordre reel place")
