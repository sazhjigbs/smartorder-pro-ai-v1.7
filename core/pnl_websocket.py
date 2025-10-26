#!/usr/bin/env python3
"""
📡 SAFELOGIC SmartOrder PRO — PNL WebSocket Live
Bybit V5 Private WebSocket pour PnL temps réel
Optimisé pour VPS faible RAM (859MB/3919MB)
"""

import os
import time
import json
import hmac
import hashlib
import threading
from datetime import datetime
from typing import Dict, Optional
import websocket  # pip install websocket-client

from core.logger import logger

# Config Bybit
API_KEY = os.getenv("BYBIT_API_KEY", "")
API_SECRET = os.getenv("BYBIT_API_SECRET", "")
WS_URL = "wss://stream.bybit.com/v5/private"

# Cache ultra-léger (RAM optimisé)
CACHE = {
    "positions": {},      # symbol -> position data
    "last_prices": {},    # symbol -> last price
    "latency_ms": 0,      # WebSocket latency
    "status": "disconnected",
    "last_update": None,
    "error": None
}

class BybitWebSocketPNL:
    """WebSocket privé pour PNL temps réel"""
    
    def __init__(self):
        self.ws = None
        self.running = False
        self.reconnect_count = 0
        self.last_ping = time.time()
        
        # Validate credentials
        if not API_KEY or not API_SECRET:
            logger.error("Missing BYBIT_API_KEY or BYBIT_API_SECRET")
            raise ValueError("Bybit credentials required")
    
    def generate_signature(self, expires: int) -> str:
        """Génère signature pour auth WebSocket"""
        param_str = f"GET/realtime{expires}"
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def on_message(self, ws, message):
        """Handler messages WebSocket"""
        try:
            data = json.loads(message)
            
            # Ping/Pong
            if data.get("op") == "pong":
                self.last_ping = time.time()
                return
            
            # Auth success
            if data.get("op") == "auth":
                if data.get("success"):
                    logger.info("WebSocket authenticated")
                    CACHE["status"] = "authenticated"
                    
                    # Subscribe to position updates
                    self.subscribe_positions()
                else:
                    logger.error(f"Auth failed: {data}")
                    CACHE["error"] = "auth_failed"
                return
            
            # Position updates
            if data.get("topic") == "position":
                self.handle_position_update(data)
            
            # Order updates (pour calcul PnL)
            elif data.get("topic") == "order":
                self.handle_order_update(data)
            
            # Execution updates
            elif data.get("topic") == "execution":
                self.handle_execution_update(data)
                
        except Exception as e:
            logger.error(f"WebSocket message error: {str(e)}")
            CACHE["error"] = str(e)
    
    def handle_position_update(self, data):
        """Traite mise à jour position"""
        try:
            for pos in data.get("data", []):
                symbol = pos.get("symbol")
                
                # Calcul PNL %
                entry_price = float(pos.get("avgPrice", 0))
                last_price = float(pos.get("markPrice", entry_price))
                size = float(pos.get("size", 0))
                side = pos.get("side", "").upper()
                leverage = float(pos.get("leverage", 1))
                unrealized_pnl = float(pos.get("unrealisedPnl", 0))
                
                # Calcul PNL %
                if entry_price > 0 and size > 0:
                    if side == "BUY":  # LONG
                        pnl_pct = ((last_price - entry_price) / entry_price) * 100 * leverage
                    else:  # SHORT
                        pnl_pct = ((entry_price - last_price) / entry_price) * 100 * leverage
                else:
                    pnl_pct = 0
                
                # Update cache (économie RAM)
                CACHE["positions"][symbol] = {
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "entry_price": entry_price,
                    "last_price": last_price,
                    "pnl_pct": round(pnl_pct, 2),
                    "pnl_usdt": round(unrealized_pnl, 2),
                    "leverage": leverage,
                    "timestamp": datetime.now().isoformat()
                }
                
                CACHE["last_prices"][symbol] = last_price
                CACHE["last_update"] = time.strftime("%H:%M:%S")
                
                # Log trade
                logger.trade(
                    side, symbol, last_price, size,
                    pnl_pct=pnl_pct,
                    pnl_usdt=unrealized_pnl
                )
                
        except Exception as e:
            logger.error(f"Position update error: {str(e)}")
    
    def handle_order_update(self, data):
        """Traite ordre (optionnel)"""
        pass
    
    def handle_execution_update(self, data):
        """Traite exécution (optionnel)"""
        pass
    
    def on_error(self, ws, error):
        """Handler erreurs"""
        logger.error(f"WebSocket error: {error}")
        CACHE["error"] = str(error)
        CACHE["status"] = "error"
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handler déconnexion"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        CACHE["status"] = "disconnected"
        
        # Auto-reconnect (avec backoff)
        if self.running:
            wait_time = min(5 * (self.reconnect_count + 1), 30)  # Max 30s
            logger.info(f"Reconnecting in {wait_time}s...")
            time.sleep(wait_time)
            self.reconnect_count += 1
            self.connect()
    
    def on_open(self, ws):
        """Handler connexion"""
        logger.info("WebSocket connected")
        CACHE["status"] = "connected"
        self.reconnect_count = 0
        
        # Auth
        expires = int(time.time() * 1000) + 10000
        signature = self.generate_signature(expires)
        
        auth_msg = {
            "op": "auth",
            "args": [API_KEY, expires, signature]
        }
        
        ws.send(json.dumps(auth_msg))
        
        # Start ping thread
        threading.Thread(target=self.ping_loop, daemon=True).start()
    
    def subscribe_positions(self):
        """Subscribe aux updates positions"""
        if not self.ws:
            return
        
        # Subscribe position + order + execution
        subscribe_msg = {
            "op": "subscribe",
            "args": [
                "position",      # Position updates
                "order",         # Order updates
                "execution"      # Execution updates
            ]
        }
        
        self.ws.send(json.dumps(subscribe_msg))
        logger.info("Subscribed to position/order/execution")
    
    def ping_loop(self):
        """Ping périodique (keep-alive)"""
        while self.running and self.ws:
            try:
                # Mesure latency
                start = time.time()
                self.ws.send(json.dumps({"op": "ping"}))
                
                # Attends pong (timeout 5s)
                time.sleep(1)
                if time.time() - self.last_ping < 5:
                    CACHE["latency_ms"] = round((time.time() - start) * 1000, 1)
                
                time.sleep(20)  # Ping toutes les 20s
                
            except Exception as e:
                logger.error(f"Ping error: {str(e)}")
                break
    
    def connect(self):
        """Connexion WebSocket"""
        if self.ws:
            self.ws.close()
        
        logger.info(f"Connecting to {WS_URL}...")
        
        self.running = True
        self.ws = websocket.WebSocketApp(
            WS_URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # Run forever (blocking)
        self.ws.run_forever()
    
    def start(self):
        """Démarre WebSocket en thread"""
        threading.Thread(target=self.connect, daemon=True).start()
        logger.info("WebSocket PNL started")
    
    def stop(self):
        """Arrête WebSocket"""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("WebSocket PNL stopped")

# Singleton global
_ws_pnl = None

def start_websocket_pnl():
    """Démarre WebSocket PNL"""
    global _ws_pnl
    
    if _ws_pnl is None:
        _ws_pnl = BybitWebSocketPNL()
        _ws_pnl.start()
        logger.info("PNL WebSocket service started")
    
    return _ws_pnl

def get_live_pnl() -> Dict:
    """Récupère PNL live depuis cache"""
    return {
        "positions": CACHE["positions"],
        "last_prices": CACHE["last_prices"],
        "latency_ms": CACHE["latency_ms"],
        "status": CACHE["status"],
        "last_update": CACHE["last_update"],
        "error": CACHE["error"]
    }

def get_position_pnl(symbol: str) -> Optional[Dict]:
    """Récupère PNL d'une position"""
    return CACHE["positions"].get(symbol)

# Test standalone
if __name__ == "__main__":
    print("🚀 Testing WebSocket PNL...")
    
    ws = start_websocket_pnl()
    
    # Wait and display
    try:
        while True:
            time.sleep(5)
            pnl = get_live_pnl()
            print(f"\n📊 Status: {pnl['status']}")
            print(f"⏱️ Latency: {pnl['latency_ms']}ms")
            print(f"📈 Positions: {len(pnl['positions'])}")
            
            for symbol, pos in pnl['positions'].items():
                print(f"  {symbol}: {pos['side']} {pos['size']} @ {pos['entry_price']}")
                print(f"    PnL: {pos['pnl_pct']}% ({pos['pnl_usdt']} USDT)")
                
    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
        ws.stop()
