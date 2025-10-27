"""
KuCoin Exchange Connector
Professional connector for KuCoin Spot & Futures trading

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import time
import hmac
import hashlib
import base64
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

LOG = logging.getLogger(__name__)


class KuCoinConnector:
    """
    KuCoin API Connector - Spot & Futures
    
    Features:
    - Spot trading
    - Futures trading
    - Rate limiting (custom per endpoint)
    - Auto retry on errors
    - Sandbox support
    """
    
    def __init__(self, 
                 api_key: str = None, 
                 api_secret: str = None,
                 passphrase: str = None,
                 sandbox: bool = False):
        """
        Initialize KuCoin connector
        
        Args:
            api_key: KuCoin API key
            api_secret: KuCoin API secret
            passphrase: KuCoin API passphrase
            sandbox: Use sandbox (default: False)
        """
        self.api_key = api_key or os.getenv("KUCOIN_API_KEY")
        self.api_secret = api_secret or os.getenv("KUCOIN_API_SECRET")
        self.passphrase = passphrase or os.getenv("KUCOIN_PASSPHRASE")
        self.sandbox = sandbox
        
        # Endpoints
        if sandbox:
            self.base_url = "https://openapi-sandbox.kucoin.com"
            self.futures_url = "https://api-sandbox-futures.kucoin.com"
        else:
            self.base_url = "https://api.kucoin.com"
            self.futures_url = "https://api-futures.kucoin.com"
        
        # Rate limiting
        self.max_requests_per_sec = 10
        self.request_timestamps = []
        
        # Retry config
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        LOG.info(f"✅ KuCoin Connector initialized (sandbox={sandbox})")
    
    def _generate_signature(self, timestamp: str, method: str, endpoint: str, body: str = '') -> str:
        """Generate signature for KuCoin API"""
        str_to_sign = timestamp + method + endpoint + body
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                str_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        )
        return signature.decode('utf-8')
    
    def _generate_passphrase_signature(self) -> str:
        """Generate passphrase signature for KuCoin API v2"""
        passphrase_signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                self.passphrase.encode('utf-8'),
                hashlib.sha256
            ).digest()
        )
        return passphrase_signature.decode('utf-8')
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()
        # Remove timestamps older than 1 second
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                   if now - ts < 1]
        
        if len(self.request_timestamps) >= self.max_requests_per_sec:
            sleep_time = 1 - (now - self.request_timestamps[0])
            LOG.warning(f"⚠️ Rate limit reached, sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    def _request(self, 
                 method: str, 
                 endpoint: str, 
                 params: Dict = None,
                 body: Dict = None,
                 futures: bool = False) -> Dict:
        """
        Make HTTP request to KuCoin API
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Query parameters
            body: Request body
            futures: Use futures API (default: False)
        
        Returns:
            Response data
        """
        self._check_rate_limit()
        
        base_url = self.futures_url if futures else self.base_url
        url = f"{base_url}{endpoint}"
        
        # Prepare request
        timestamp = str(int(time.time() * 1000))
        
        body_str = ''
        if body:
            import json
            body_str = json.dumps(body)
        
        # Build signature string
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
            endpoint_with_params = f"{endpoint}?{query_string}"
        else:
            endpoint_with_params = endpoint
        
        signature = self._generate_signature(timestamp, method, endpoint_with_params, body_str)
        passphrase = self._generate_passphrase_signature()
        
        headers = {
            'KC-API-KEY': self.api_key,
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-KEY-VERSION': '2',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, json=body, headers=headers, timeout=10)
                elif method == 'DELETE':
                    response = requests.delete(url, params=params, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                data = response.json()
                
                # KuCoin returns {code, msg, data}
                if data.get('code') != '200000':
                    raise Exception(f"KuCoin API error: {data.get('msg')}")
                
                return data.get('data', {})
            
            except requests.exceptions.RequestException as e:
                LOG.error(f"❌ KuCoin API error (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    def test_connection(self) -> Dict:
        """Test connectivity to KuCoin API"""
        try:
            # Test public endpoint (no auth required)
            url = f"{self.base_url}/api/v1/timestamp"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            return {
                'success': True,
                'exchange': 'kucoin',
                'server_time': data.get('data'),
                'sandbox': self.sandbox
            }
        except Exception as e:
            LOG.error(f"❌ Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_balance(self, account_type: str = 'trade') -> Dict:
        """
        Get account balance
        
        Args:
            account_type: 'trade' (spot) or 'main'
        
        Returns:
            Balance data
        """
        try:
            # Spot balance
            params = {
                'type': account_type
            }
            data = self._request('GET', '/api/v1/accounts', params=params)
            
            balances = []
            total_equity = 0.0
            
            for account in data:
                available = float(account.get('available', 0))
                holds = float(account.get('holds', 0))
                balance = float(account.get('balance', 0))
                
                if balance > 0:
                    balances.append({
                        'coin': account['currency'],
                        'available': available,
                        'holds': holds,
                        'total': balance
                    })
                    
                    # Rough USDT conversion
                    if account['currency'] in ['USDT', 'USDC', 'DAI']:
                        total_equity += balance
            
            return {
                'success': True,
                'account_type': account_type,
                'balances': balances,
                'total_equity': total_equity
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to get balance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker data for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
        
        Returns:
            Ticker data
        """
        try:
            params = {
                'symbol': symbol
            }
            data = self._request('GET', '/api/v1/market/orderbook/level1', params=params)
            
            return {
                'success': True,
                'symbol': symbol,
                'last_price': float(data.get('price', 0)),
                'bid_price': float(data.get('bestBid', 0)),
                'ask_price': float(data.get('bestAsk', 0)),
                'timestamp': int(data.get('time', 0))
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to get ticker for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def place_order(self,
                    symbol: str,
                    side: str,
                    order_type: str,
                    quantity: float = None,
                    price: float = None,
                    funds: float = None) -> Dict:
        """
        Place an order
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: Order quantity (for limit or market sell)
            price: Limit price (required for limit orders)
            funds: Funds (for market buy orders)
        
        Returns:
            Order result
        """
        try:
            import uuid
            
            body = {
                'clientOid': str(uuid.uuid4()),
                'symbol': symbol,
                'side': side.lower(),
                'type': order_type.lower()
            }
            
            if order_type.lower() == 'limit':
                if not price or not quantity:
                    raise ValueError("Price and quantity required for limit orders")
                body['price'] = str(price)
                body['size'] = str(quantity)
            
            elif order_type.lower() == 'market':
                if side.lower() == 'buy':
                    if not funds:
                        raise ValueError("Funds required for market buy orders")
                    body['funds'] = str(funds)
                else:
                    if not quantity:
                        raise ValueError("Quantity required for market sell orders")
                    body['size'] = str(quantity)
            
            data = self._request('POST', '/api/v1/orders', body=body)
            
            return {
                'success': True,
                'order_id': data.get('orderId'),
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'price': price or 0
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to place order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Cancellation result
        """
        try:
            data = self._request('DELETE', f'/api/v1/orders/{order_id}')
            
            return {
                'success': True,
                'cancelled_order_ids': data.get('cancelledOrderIds', [])
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to cancel order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_positions(self) -> List[Dict]:
        """
        Get open positions (Futures only)
        
        Returns:
            List of positions
        """
        try:
            data = self._request('GET', '/api/v1/positions', futures=True)
            
            positions = []
            for pos in data:
                if float(pos.get('currentQty', 0)) != 0:
                    positions.append({
                        'symbol': pos['symbol'],
                        'size': abs(float(pos.get('currentQty', 0))),
                        'side': 'Long' if float(pos.get('currentQty', 0)) > 0 else 'Short',
                        'entry_price': float(pos.get('avgEntryPrice', 0)),
                        'mark_price': float(pos.get('markPrice', 0)),
                        'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                        'leverage': int(pos.get('realLeverage', 1))
                    })
            
            return positions
        
        except Exception as e:
            LOG.error(f"❌ Failed to get positions: {e}")
            return []
    
    def close_position(self, symbol: str) -> Dict:
        """
        Close a position (Futures only)
        
        Args:
            symbol: Symbol to close
        
        Returns:
            Close result
        """
        try:
            # Get current position
            positions = self.get_positions()
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not position:
                return {
                    'success': False,
                    'error': f'No open position for {symbol}'
                }
            
            # Close by placing opposite market order
            import uuid
            
            body = {
                'clientOid': str(uuid.uuid4()),
                'symbol': symbol,
                'type': 'market',
                'side': 'sell' if position['side'] == 'Long' else 'buy',
                'closeOrder': True,
                'size': int(position['size'])
            }
            
            data = self._request('POST', '/api/v1/orders', body=body, futures=True)
            
            return {
                'success': True,
                'order_id': data.get('orderId')
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to close position: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    connector = KuCoinConnector(sandbox=True)
    
    # Test connection
    print("Testing connection...")
    result = connector.test_connection()
    print(f"Connection: {result}")
    
    # Test ticker
    print("\nTesting ticker...")
    ticker = connector.get_ticker('BTC-USDT')
    print(f"BTC Price: ${ticker.get('last_price', 'N/A')}")
