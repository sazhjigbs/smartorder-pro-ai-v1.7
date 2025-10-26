#!/usr/bin/env python3
"""
SmartOrder PRO - Bybit Private WebSocket Client
================================================
WebSocket privé pour streaming temps réel:
- Positions (ouverture, modification, fermeture)
- Ordres (placement, exécution, annulation)
- Wallet (changements balance)
- Execution (trades exécutés)

Usage:
    from web.portal_v5_pro.ws_private import PrivateWSClient
    
    client = PrivateWSClient()
    await client.connect()
    await client.subscribe_positions()
"""

import asyncio
import json
import hmac
import hashlib
import time
from typing import Callable, Dict, Any, Optional
import websockets
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Bybit WebSocket URLs
WS_PRIVATE_MAINNET = "wss://stream.bybit.com/v5/private"
WS_PRIVATE_TESTNET = "wss://stream-testnet.bybit.com/v5/private"


class PrivateWSClient:
    """Client WebSocket privé Bybit V5"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = False
    ):
        """
        Initialise le client WebSocket privé
        
        Args:
            api_key: Clé API Bybit
            api_secret: Secret API Bybit
            testnet: True pour testnet, False pour mainnet
        """
        self.api_key = api_key or os.getenv("BYBIT_API_KEY")
        self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET")
        self.testnet = testnet
        
        self.ws_url = WS_PRIVATE_TESTNET if testnet else WS_PRIVATE_MAINNET
        self.ws = None
        self.is_connected = False
        self.is_authenticated = False
        
        # Callbacks
        self.on_position = None
        self.on_order = None
        self.on_execution = None
        self.on_wallet = None
        self.on_error = None
        
        # Data cache
        self.positions = {}
        self.orders = {}
        self.balance = {}
        
        # Heartbeat
        self.last_pong = time.time()
        self.ping_interval = 20  # secondes
    
    def _generate_signature(self, expires: int) -> str:
        """
        Génère signature HMAC pour auth
        
        Args:
            expires: Timestamp expiration (ms)
        
        Returns:
            Signature hexadécimale
        """
        param_str = f"GET/realtime{expires}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def connect(self):
        """Connecte au WebSocket"""
        try:
            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=None  # Géré manuellement
            )
            self.is_connected = True
            print(f"✅ WebSocket connecté: {self.ws_url}")
            
            # Authentifier
            await self._authenticate()
            
            # Démarrer heartbeat
            asyncio.create_task(self._heartbeat())
            
            # Démarrer lecture messages
            asyncio.create_task(self._listen())
            
        except Exception as e:
            print(f"❌ Erreur connexion WebSocket: {e}")
            self.is_connected = False
            if self.on_error:
                await self.on_error(str(e))
    
    async def _authenticate(self):
        """Authentifie la connexion WebSocket"""
        try:
            # Timestamp expiration (5 secondes)
            expires = int((time.time() + 5) * 1000)
            signature = self._generate_signature(expires)
            
            auth_message = {
                "op": "auth",
                "args": [self.api_key, expires, signature]
            }
            
            await self.ws.send(json.dumps(auth_message))
            print("🔐 Authentification envoyée...")
            
        except Exception as e:
            print(f"❌ Erreur authentification: {e}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _heartbeat(self):
        """Envoie ping toutes les 20 secondes"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.ping_interval)
                
                if self.ws and not self.ws.closed:
                    ping_msg = {"op": "ping"}
                    await self.ws.send(json.dumps(ping_msg))
                    
                    # Check si pong reçu
                    if time.time() - self.last_pong > 60:
                        print("⚠️ Pas de pong depuis 60s, reconnexion...")
                        await self.reconnect()
                
            except Exception as e:
                print(f"❌ Erreur heartbeat: {e}")
    
    async def _listen(self):
        """Écoute les messages WebSocket"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self._handle_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            print("⚠️ Connexion WebSocket fermée")
            self.is_connected = False
            await self.reconnect()
            
        except Exception as e:
            print(f"❌ Erreur lecture WebSocket: {e}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Traite les messages reçus
        
        Args:
            data: Message JSON reçu
        """
        try:
            # Réponse auth
            if data.get("op") == "auth":
                if data.get("success"):
                    self.is_authenticated = True
                    print("✅ Authentifié avec succès")
                else:
                    print(f"❌ Échec authentification: {data.get('ret_msg')}")
            
            # Pong (heartbeat)
            elif data.get("op") == "pong":
                self.last_pong = time.time()
            
            # Topic subscription confirmée
            elif data.get("op") == "subscribe":
                if data.get("success"):
                    print(f"✅ Souscription réussie: {data.get('req_id')}")
            
            # Data topic
            elif data.get("topic"):
                topic = data["topic"]
                
                # Positions
                if topic.startswith("position"):
                    await self._handle_position(data)
                
                # Orders
                elif topic.startswith("order"):
                    await self._handle_order(data)
                
                # Executions (trades)
                elif topic.startswith("execution"):
                    await self._handle_execution(data)
                
                # Wallet
                elif topic.startswith("wallet"):
                    await self._handle_wallet(data)
        
        except Exception as e:
            print(f"❌ Erreur traitement message: {e}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _handle_position(self, data: Dict[str, Any]):
        """Traite les updates positions"""
        try:
            positions_data = data.get("data", [])
            
            for pos in positions_data:
                symbol = pos.get("symbol")
                side = pos.get("side")
                size = float(pos.get("size", 0))
                entry_price = float(pos.get("avgPrice", 0))
                mark_price = float(pos.get("markPrice", 0))
                unrealised_pnl = float(pos.get("unrealisedPnl", 0))
                
                # Calculer PnL %
                if entry_price > 0:
                    if side == "Buy":
                        pnl_pct = ((mark_price - entry_price) / entry_price) * 100
                    else:
                        pnl_pct = ((entry_price - mark_price) / entry_price) * 100
                else:
                    pnl_pct = 0
                
                # Update cache
                self.positions[symbol] = {
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "entry_price": entry_price,
                    "mark_price": mark_price,
                    "unrealised_pnl": unrealised_pnl,
                    "pnl_percent": round(pnl_pct, 2),
                    "leverage": float(pos.get("leverage", 0)),
                    "liq_price": float(pos.get("liqPrice", 0)),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Callback
                if self.on_position:
                    await self.on_position(self.positions[symbol])
        
        except Exception as e:
            print(f"❌ Erreur traitement position: {e}")
    
    async def _handle_order(self, data: Dict[str, Any]):
        """Traite les updates ordres"""
        try:
            orders_data = data.get("data", [])
            
            for order in orders_data:
                order_id = order.get("orderId")
                
                self.orders[order_id] = {
                    "order_id": order_id,
                    "symbol": order.get("symbol"),
                    "side": order.get("side"),
                    "order_type": order.get("orderType"),
                    "price": float(order.get("price", 0)),
                    "qty": float(order.get("qty", 0)),
                    "status": order.get("orderStatus"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Callback
                if self.on_order:
                    await self.on_order(self.orders[order_id])
        
        except Exception as e:
            print(f"❌ Erreur traitement order: {e}")
    
    async def _handle_execution(self, data: Dict[str, Any]):
        """Traite les executions (trades)"""
        try:
            executions = data.get("data", [])
            
            for execution in executions:
                exec_data = {
                    "exec_id": execution.get("execId"),
                    "order_id": execution.get("orderId"),
                    "symbol": execution.get("symbol"),
                    "side": execution.get("side"),
                    "price": float(execution.get("execPrice", 0)),
                    "qty": float(execution.get("execQty", 0)),
                    "fee": float(execution.get("execFee", 0)),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Callback
                if self.on_execution:
                    await self.on_execution(exec_data)
        
        except Exception as e:
            print(f"❌ Erreur traitement execution: {e}")
    
    async def _handle_wallet(self, data: Dict[str, Any]):
        """Traite les updates wallet"""
        try:
            wallet_data = data.get("data", [])
            
            for wallet in wallet_data:
                coin = wallet.get("coin")
                
                self.balance[coin] = {
                    "coin": coin,
                    "equity": float(wallet.get("equity", 0)),
                    "available": float(wallet.get("availableToWithdraw", 0)),
                    "wallet_balance": float(wallet.get("walletBalance", 0)),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Callback
                if self.on_wallet:
                    await self.on_wallet(self.balance[coin])
        
        except Exception as e:
            print(f"❌ Erreur traitement wallet: {e}")
    
    async def subscribe_positions(self):
        """Souscrit aux updates positions"""
        if not self.is_authenticated:
            print("⚠️ Pas authentifié, attente...")
            await asyncio.sleep(2)
        
        sub_message = {
            "op": "subscribe",
            "args": ["position"]
        }
        await self.ws.send(json.dumps(sub_message))
        print("📡 Souscription positions envoyée")
    
    async def subscribe_orders(self):
        """Souscrit aux updates ordres"""
        sub_message = {
            "op": "subscribe",
            "args": ["order"]
        }
        await self.ws.send(json.dumps(sub_message))
        print("📡 Souscription orders envoyée")
    
    async def subscribe_executions(self):
        """Souscrit aux executions"""
        sub_message = {
            "op": "subscribe",
            "args": ["execution"]
        }
        await self.ws.send(json.dumps(sub_message))
        print("📡 Souscription executions envoyée")
    
    async def subscribe_wallet(self):
        """Souscrit aux updates wallet"""
        sub_message = {
            "op": "subscribe",
            "args": ["wallet"]
        }
        await self.ws.send(json.dumps(sub_message))
        print("📡 Souscription wallet envoyée")
    
    async def subscribe_all(self):
        """Souscrit à tous les topics"""
        await self.subscribe_positions()
        await asyncio.sleep(0.1)
        await self.subscribe_orders()
        await asyncio.sleep(0.1)
        await self.subscribe_executions()
        await asyncio.sleep(0.1)
        await self.subscribe_wallet()
    
    async def reconnect(self):
        """Reconnecte au WebSocket"""
        print("🔄 Reconnexion WebSocket...")
        self.is_connected = False
        self.is_authenticated = False
        
        if self.ws:
            await self.ws.close()
        
        await asyncio.sleep(2)
        await self.connect()
    
    async def close(self):
        """Ferme la connexion WebSocket"""
        self.is_connected = False
        if self.ws:
            await self.ws.close()
        print("👋 WebSocket fermé")
    
    def get_positions(self) -> Dict[str, Any]:
        """Retourne toutes les positions en cache"""
        return self.positions
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retourne une position spécifique"""
        return self.positions.get(symbol)
    
    def get_balance(self) -> Dict[str, Any]:
        """Retourne le balance en cache"""
        return self.balance


# ==============================================================================
# EXEMPLE D'UTILISATION
# ==============================================================================

async def example_usage():
    """Exemple d'utilisation du client WS privé"""
    
    # Créer client
    client = PrivateWSClient()
    
    # Définir callbacks
    async def on_position_update(position):
        symbol = position["symbol"]
        pnl_pct = position["pnl_percent"]
        color = "🟢" if pnl_pct > 0 else "🔴"
        print(f"{color} Position {symbol}: {pnl_pct:+.2f}%")
    
    async def on_order_update(order):
        print(f"📝 Order {order['order_id']}: {order['status']}")
    
    async def on_execution(execution):
        print(f"⚡ Execution: {execution['side']} {execution['qty']} @ {execution['price']}")
    
    client.on_position = on_position_update
    client.on_order = on_order_update
    client.on_execution = on_execution
    
    # Connecter
    await client.connect()
    await asyncio.sleep(2)  # Attendre auth
    
    # Souscrire
    await client.subscribe_all()
    
    # Garder actif
    try:
        while True:
            await asyncio.sleep(1)
            
            # Afficher positions toutes les 10s
            if int(time.time()) % 10 == 0:
                positions = client.get_positions()
                if positions:
                    print(f"\n📊 {len(positions)} positions actives:")
                    for pos in positions.values():
                        print(f"  {pos['symbol']}: {pos['pnl_percent']:+.2f}%")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt...")
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
