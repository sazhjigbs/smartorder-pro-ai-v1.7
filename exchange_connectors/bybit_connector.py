"""
SmartOrder PRO - Bybit Connector
Connexion réelle au wallet Bybit avec trading live
by MAIGA ABOUBACAR

Features:
- Lecture balance wallet en temps réel
- Exécution ordres réels (market/limit)
- Gestion positions spot & futures
- Retry automatique si échec
- Rate limiting intelligent
- WebSocket pour updates live
"""

from pybit.unified_trading import HTTP, WebSocket
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import hmac
from collections import defaultdict

LOG = logging.getLogger("exchange.bybit")

class BybitConnector:
    """
    Connecteur professionnel Bybit
    
    Gère:
    - Trading spot & futures
    - Lecture wallet balance
    - Positions ouvertes
    - Historique trades
    - WebSocket live updates
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Initialize Bybit Connector
        
        Args:
            api_key: API Key Bybit
            api_secret: API Secret Bybit
            testnet: True pour testnet, False pour mainnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # HTTP Client
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # WebSocket Client (optionnel)
        self.ws = None
        
        # Rate limiting
        self.request_count = defaultdict(int)
        self.rate_limit_window = 60  # 1 minute
        self.max_requests_per_minute = 100
        
        # Retry config
        self.max_retries = 3
        self.retry_delay = 1  # secondes
        
        # Cache
        self.balance_cache = {}
        self.positions_cache = {}
        self.cache_ttl = 5  # secondes
        
        LOG.info(f"✅ Bybit Connector initialized (testnet={testnet})")
    
    def _check_rate_limit(self) -> bool:
        """Vérifie rate limit"""
        current_minute = int(time.time() / 60)
        
        if self.request_count[current_minute] >= self.max_requests_per_minute:
            LOG.warning("⚠️ Rate limit reached, waiting...")
            time.sleep(2)
            return False
        
        self.request_count[current_minute] += 1
        return True
    
    def _retry_request(self, func, *args, **kwargs):
        """Execute request avec retry automatique"""
        for attempt in range(self.max_retries):
            try:
                self._check_rate_limit()
                result = func(*args, **kwargs)
                
                # Check response
                if isinstance(result, dict):
                    if result.get('retCode') == 0:
                        return result
                    else:
                        error_msg = result.get('retMsg', 'Unknown error')
                        LOG.error(f"❌ Bybit API error: {error_msg}")
                        
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        else:
                            raise Exception(f"Bybit API error: {error_msg}")
                
                return result
                
            except Exception as e:
                LOG.error(f"❌ Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    # ==================== WALLET BALANCE ====================
    
    def get_wallet_balance(self, account_type: str = "UNIFIED") -> Dict:
        """
        Récupère balance du wallet
        
        Args:
            account_type: "UNIFIED" | "CONTRACT" | "SPOT"
            
        Returns:
            {
                'total_equity': float,
                'available_balance': float,
                'coins': {
                    'USDT': {'balance': 1000.0, 'available': 950.0},
                    'BTC': {'balance': 0.5, 'available': 0.5}
                }
            }
        """
        try:
            # Check cache
            cache_key = f"balance_{account_type}"
            if cache_key in self.balance_cache:
                cached_data, cached_time = self.balance_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return cached_data
            
            response = self._retry_request(
                self.session.get_wallet_balance,
                accountType=account_type
            )
            
            if response['retCode'] != 0:
                LOG.error(f"Failed to get balance: {response['retMsg']}")
                return {}
            
            # Parse response
            result_list = response['result'].get('list', [])
            
            if not result_list:
                return {
                    'total_equity': 0.0,
                    'available_balance': 0.0,
                    'coins': {}
                }
            
            account_data = result_list[0]
            
            total_equity = float(account_data.get('totalEquity', 0))
            available_balance = float(account_data.get('totalAvailableBalance', 0))
            
            coins = {}
            for coin_data in account_data.get('coin', []):
                coin = coin_data['coin']
                coins[coin] = {
                    'balance': float(coin_data.get('walletBalance', 0)),
                    'available': float(coin_data.get('availableToWithdraw', 0)),
                    'equity': float(coin_data.get('equity', 0)),
                    'usd_value': float(coin_data.get('usdValue', 0))
                }
            
            result = {
                'total_equity': total_equity,
                'available_balance': available_balance,
                'coins': coins,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update cache
            self.balance_cache[cache_key] = (result, time.time())
            
            LOG.info(f"✅ Balance retrieved: ${total_equity:.2f} equity")
            
            return result
            
        except Exception as e:
            LOG.error(f"❌ Error getting wallet balance: {e}")
            return {}
    
    # ==================== MARKET DATA ====================
    
    def get_ticker_price(self, symbol: str, category: str = "spot") -> float:
        """
        Récupère le prix actuel d'un symbol
        
        Args:
            symbol: Symbol (ex: BTCUSDT)
            category: "spot" | "linear" | "inverse"
            
        Returns:
            Prix actuel (float)
        """
        try:
            response = self._retry_request(
                self.session.get_tickers,
                category=category,
                symbol=symbol
            )
            
            if response['retCode'] != 0:
                return 0.0
            
            ticker_list = response['result'].get('list', [])
            if ticker_list:
                return float(ticker_list[0].get('lastPrice', 0))
            
            return 0.0
            
        except Exception as e:
            LOG.error(f"❌ Error getting ticker price: {e}")
            return 0.0
    
    def get_orderbook(self, symbol: str, category: str = "spot", limit: int = 25) -> Dict:
        """
        Récupère l'orderbook
        
        Args:
            symbol: Symbol
            category: "spot" | "linear"
            limit: Depth (25, 50, 100, 200)
            
        Returns:
            {'bids': [[price, qty], ...], 'asks': [[price, qty], ...]}
        """
        try:
            response = self._retry_request(
                self.session.get_orderbook,
                category=category,
                symbol=symbol,
                limit=limit
            )
            
            if response['retCode'] != 0:
                return {'bids': [], 'asks': []}
            
            orderbook = response['result']
            
            return {
                'bids': [[float(b[0]), float(b[1])] for b in orderbook.get('b', [])],
                'asks': [[float(a[0]), float(a[1])] for a in orderbook.get('a', [])],
                'timestamp': orderbook.get('ts', 0)
            }
            
        except Exception as e:
            LOG.error(f"❌ Error getting orderbook: {e}")
            return {'bids': [], 'asks': []}
    
    # ==================== TRADING ====================
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        price: Optional[float] = None,
        category: str = "spot",
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> Dict:
        """
        Place un ordre réel sur Bybit
        
        Args:
            symbol: Symbol (BTCUSDT)
            side: "Buy" | "Sell"
            order_type: "Market" | "Limit"
            qty: Quantité
            price: Prix (requis pour Limit)
            category: "spot" | "linear" | "inverse"
            time_in_force: "GTC" | "IOC" | "FOK"
            reduce_only: True pour fermer position seulement
            
        Returns:
            {
                'success': bool,
                'order_id': str,
                'order_link_id': str,
                'symbol': str,
                'side': str,
                'price': float,
                'qty': float,
                'status': str
            }
        """
        try:
            LOG.info(f"🔥 Placing order: {side} {qty} {symbol} @ {order_type}")
            
            # Validation
            if order_type == "Limit" and price is None:
                raise ValueError("Price required for Limit orders")
            
            # Préparer params
            params = {
                'category': category,
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': str(qty),
                'timeInForce': time_in_force
            }
            
            if price:
                params['price'] = str(price)
            
            if reduce_only:
                params['reduceOnly'] = True
            
            # Execute order
            response = self._retry_request(
                self.session.place_order,
                **params
            )
            
            if response['retCode'] != 0:
                LOG.error(f"❌ Order failed: {response['retMsg']}")
                return {
                    'success': False,
                    'error': response['retMsg']
                }
            
            result = response['result']
            
            order_result = {
                'success': True,
                'order_id': result.get('orderId'),
                'order_link_id': result.get('orderLinkId'),
                'symbol': symbol,
                'side': side,
                'order_type': order_type,
                'price': float(price) if price else 0.0,
                'qty': qty,
                'status': 'submitted',
                'timestamp': datetime.now().isoformat()
            }
            
            LOG.info(f"✅ Order placed successfully: {order_result['order_id']}")
            
            return order_result
            
        except Exception as e:
            LOG.error(f"❌ Error placing order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, symbol: str, order_id: str, category: str = "spot") -> bool:
        """
        Annule un ordre
        
        Args:
            symbol: Symbol
            order_id: Order ID
            category: "spot" | "linear"
            
        Returns:
            True si succès
        """
        try:
            response = self._retry_request(
                self.session.cancel_order,
                category=category,
                symbol=symbol,
                orderId=order_id
            )
            
            if response['retCode'] == 0:
                LOG.info(f"✅ Order cancelled: {order_id}")
                return True
            else:
                LOG.error(f"❌ Cancel failed: {response['retMsg']}")
                return False
                
        except Exception as e:
            LOG.error(f"❌ Error cancelling order: {e}")
            return False
    
    def get_open_orders(self, symbol: Optional[str] = None, category: str = "spot") -> List[Dict]:
        """
        Récupère les ordres ouverts
        
        Args:
            symbol: Symbol (optional, None = tous)
            category: "spot" | "linear"
            
        Returns:
            Liste d'ordres ouverts
        """
        try:
            params = {'category': category}
            if symbol:
                params['symbol'] = symbol
            
            response = self._retry_request(
                self.session.get_open_orders,
                **params
            )
            
            if response['retCode'] != 0:
                return []
            
            orders = []
            for order in response['result'].get('list', []):
                orders.append({
                    'order_id': order.get('orderId'),
                    'symbol': order.get('symbol'),
                    'side': order.get('side'),
                    'order_type': order.get('orderType'),
                    'price': float(order.get('price', 0)),
                    'qty': float(order.get('qty', 0)),
                    'filled_qty': float(order.get('cumExecQty', 0)),
                    'status': order.get('orderStatus'),
                    'created_time': order.get('createdTime')
                })
            
            return orders
            
        except Exception as e:
            LOG.error(f"❌ Error getting open orders: {e}")
            return []
    
    # ==================== POSITIONS ====================
    
    def get_positions(self, symbol: Optional[str] = None, category: str = "linear") -> List[Dict]:
        """
        Récupère les positions ouvertes
        
        Args:
            symbol: Symbol (optional)
            category: "linear" | "inverse"
            
        Returns:
            Liste des positions
        """
        try:
            params = {'category': category, 'settleCoin': 'USDT'}
            if symbol:
                params['symbol'] = symbol
            
            response = self._retry_request(
                self.session.get_positions,
                **params
            )
            
            if response['retCode'] != 0:
                return []
            
            positions = []
            for pos in response['result'].get('list', []):
                size = float(pos.get('size', 0))
                
                if size > 0:  # Seulement positions actives
                    positions.append({
                        'symbol': pos.get('symbol'),
                        'side': pos.get('side'),
                        'size': size,
                        'entry_price': float(pos.get('avgPrice', 0)),
                        'mark_price': float(pos.get('markPrice', 0)),
                        'leverage': float(pos.get('leverage', 1)),
                        'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                        'realized_pnl': float(pos.get('cumRealisedPnl', 0)),
                        'position_value': float(pos.get('positionValue', 0))
                    })
            
            return positions
            
        except Exception as e:
            LOG.error(f"❌ Error getting positions: {e}")
            return []
    
    def close_position(self, symbol: str, category: str = "linear") -> bool:
        """
        Ferme une position
        
        Args:
            symbol: Symbol
            category: "linear" | "inverse"
            
        Returns:
            True si succès
        """
        try:
            # Récupérer position actuelle
            positions = self.get_positions(symbol=symbol, category=category)
            
            if not positions:
                LOG.warning(f"No position to close for {symbol}")
                return False
            
            position = positions[0]
            
            # Ordre inverse pour fermer
            close_side = "Sell" if position['side'] == "Buy" else "Buy"
            
            result = self.place_order(
                symbol=symbol,
                side=close_side,
                order_type="Market",
                qty=position['size'],
                category=category,
                reduce_only=True
            )
            
            if result['success']:
                LOG.info(f"✅ Position closed: {symbol}")
                return True
            else:
                LOG.error(f"❌ Failed to close position: {result.get('error')}")
                return False
                
        except Exception as e:
            LOG.error(f"❌ Error closing position: {e}")
            return False
    
    # ==================== UTILS ====================
    
    def get_server_time(self) -> int:
        """Récupère server time Bybit"""
        try:
            response = self._retry_request(self.session.get_server_time)
            return int(response['result']['timeNano']) // 1000000
        except:
            return int(time.time() * 1000)
    
    def test_connection(self) -> bool:
        """Test connexion à Bybit"""
        try:
            response = self._retry_request(self.session.get_server_time)
            if response['retCode'] == 0:
                LOG.info("✅ Bybit connection OK")
                return True
            else:
                LOG.error("❌ Bybit connection FAILED")
                return False
        except Exception as e:
            LOG.error(f"❌ Connection test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict:
        """Récupère info compte"""
        try:
            response = self._retry_request(self.session.get_api_key_information)
            
            if response['retCode'] == 0:
                result = response['result']
                return {
                    'user_id': result.get('userId'),
                    'permissions': result.get('permissions', {}),
                    'read_only': result.get('readOnly', 0),
                    'ips': result.get('ips', []),
                    'note': result.get('note', '')
                }
            else:
                return {}
                
        except Exception as e:
            LOG.error(f"❌ Error getting account info: {e}")
            return {}


# Factory function
def create_bybit_connector(api_key: str, api_secret: str, testnet: bool = False) -> BybitConnector:
    """
    Crée une instance de BybitConnector
    
    Args:
        api_key: API Key
        api_secret: API Secret
        testnet: True pour testnet
        
    Returns:
        BybitConnector instance
    """
    return BybitConnector(api_key, api_secret, testnet)


if __name__ == "__main__":
    print("=" * 60)
    print("🔌 SmartOrder PRO - Bybit Connector")
    print("by MAIGA ABOUBACAR")
    print("=" * 60)
    
    # Test avec clés depuis .env
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        print("\n❌ API keys not found in .env")
        print("   Add: BYBIT_API_KEY=xxx and BYBIT_API_SECRET=xxx")
        exit(1)
    
    connector = BybitConnector(api_key, api_secret, testnet=True)
    
    print("\n✅ Test 1: Connection")
    if connector.test_connection():
        print("   Connected successfully!")
    
    print("\n✅ Test 2: Account Info")
    info = connector.get_account_info()
    if info:
        print(f"   User ID: {info.get('user_id')}")
        print(f"   Permissions: {info.get('permissions')}")
    
    print("\n✅ Test 3: Wallet Balance")
    balance = connector.get_wallet_balance()
    if balance:
        print(f"   Total Equity: ${balance['total_equity']:.2f}")
        print(f"   Available: ${balance['available_balance']:.2f}")
        print(f"   Coins: {list(balance['coins'].keys())}")
    
    print("\n✅ Test 4: Ticker Price")
    btc_price = connector.get_ticker_price('BTCUSDT')
    print(f"   BTC Price: ${btc_price:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Bybit Connector Ready!")
    print("=" * 60)
