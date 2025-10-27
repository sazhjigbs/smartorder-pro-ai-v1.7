"""
OKX Exchange Connector
Professional connector for OKX Spot & Futures trading

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


class OKXConnector:
    """
    OKX API Connector - Spot & Futures
    
    Features:
    - Spot trading
    - Futures (SWAP)
    - Rate limiting (20 req/2sec)
    - Auto retry on errors
    - Demo trading support
    """
    
    def __init__(self, 
                 api_key: str = None, 
                 api_secret: str = None,
                 passphrase: str = None,
                 demo: bool = False):
        """
        Initialize OKX connector
        
        Args:
            api_key: OKX API key
            api_secret: OKX API secret
            passphrase: OKX API passphrase
            demo: Use demo trading (default: False)
        """
        self.api_key = api_key or os.getenv("OKX_API_KEY")
        self.api_secret = api_secret or os.getenv("OKX_API_SECRET")
        self.passphrase = passphrase or os.getenv("OKX_PASSPHRASE")
        self.demo = demo
        
        # Endpoints
        if demo:
            self.base_url = "https://www.okx.com"  # Demo uses same URL with flag
        else:
            self.base_url = "https://www.okx.com"
        
        # Rate limiting
        self.max_requests_per_2sec = 20
        self.request_timestamps = []
        
        # Retry config
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        LOG.info(f"✅ OKX Connector initialized (demo={demo})")
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """Generate signature for OKX API"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()
        # Remove timestamps older than 2 seconds
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                   if now - ts < 2]
        
        if len(self.request_timestamps) >= self.max_requests_per_2sec:
            sleep_time = 2 - (now - self.request_timestamps[0])
            LOG.warning(f"⚠️ Rate limit reached, sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    def _request(self, 
                 method: str, 
                 endpoint: str, 
                 params: Dict = None,
                 body: Dict = None) -> Dict:
        """
        Make HTTP request to OKX API
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            params: Query parameters
            body: Request body
        
        Returns:
            Response data
        """
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        # Prepare request
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        
        request_path = endpoint
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            request_path += f"?{query_string}"
        
        body_str = ''
        if body:
            import json
            body_str = json.dumps(body)
        
        signature = self._generate_signature(timestamp, method, endpoint, body_str)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        if self.demo:
            headers['x-simulated-trading'] = '1'
        
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, json=body, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                data = response.json()
                
                # OKX returns {code, msg, data}
                if data.get('code') != '0':
                    raise Exception(f"OKX API error: {data.get('msg')}")
                
                return data.get('data', [])
            
            except requests.exceptions.RequestException as e:
                LOG.error(f"❌ OKX API error (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    def test_connection(self) -> Dict:
        """Test connectivity to OKX API"""
        try:
            # Test public endpoint
            data = self._request('GET', '/api/v5/public/time')
            
            return {
                'success': True,
                'exchange': 'okx',
                'server_time': data[0].get('ts') if data else None,
                'demo': self.demo
            }
        except Exception as e:
            LOG.error(f"❌ Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Balance data
        """
        try:
            data = self._request('GET', '/api/v5/account/balance')
            
            if not data:
                return {
                    'success': False,
                    'error': 'No balance data'
                }
            
            account = data[0]
            total_equity = float(account.get('totalEq', 0))
            
            balances = []
            for detail in account.get('details', []):
                available = float(detail.get('availBal', 0))
                frozen = float(detail.get('frozenBal', 0))
                
                if available > 0 or frozen > 0:
                    balances.append({
                        'coin': detail['ccy'],
                        'available': available,
                        'frozen': frozen,
                        'total': available + frozen
                    })
            
            return {
                'success': True,
                'total_equity': total_equity,
                'balances': balances
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to get balance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ticker(self, symbol: str, inst_type: str = 'SPOT') -> Dict:
        """
        Get ticker data for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            inst_type: 'SPOT' or 'SWAP'
        
        Returns:
            Ticker data
        """
        try:
            params = {
                'instId': symbol
            }
            data = self._request('GET', '/api/v5/market/ticker', params=params)
            
            if not data:
                return {
                    'success': False,
                    'error': 'No ticker data'
                }
            
            ticker = data[0]
            
            return {
                'success': True,
                'symbol': symbol,
                'last_price': float(ticker['last']),
                'bid_price': float(ticker['bidPx']),
                'ask_price': float(ticker['askPx']),
                'high_24h': float(ticker['high24h']),
                'low_24h': float(ticker['low24h']),
                'volume_24h': float(ticker['vol24h'])
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
                    quantity: float,
                    price: float = None,
                    inst_type: str = 'SPOT',
                    trade_mode: str = 'cash') -> Dict:
        """
        Place an order
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: Order quantity
            price: Limit price (required for limit orders)
            inst_type: 'SPOT' or 'SWAP'
            trade_mode: 'cash' (spot) or 'cross'/'isolated' (margin)
        
        Returns:
            Order result
        """
        try:
            body = {
                'instId': symbol,
                'tdMode': trade_mode,
                'side': side.lower(),
                'ordType': order_type.lower(),
                'sz': str(quantity)
            }
            
            if order_type.lower() == 'limit':
                if not price:
                    raise ValueError("Price required for limit orders")
                body['px'] = str(price)
            
            data = self._request('POST', '/api/v5/trade/order', body=body)
            
            if not data:
                return {
                    'success': False,
                    'error': 'No order response'
                }
            
            result = data[0]
            
            return {
                'success': True,
                'order_id': result['ordId'],
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'price': price or 0,
                'status': result.get('sCode')
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to place order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self,
                     symbol: str,
                     order_id: str) -> Dict:
        """
        Cancel an order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
        
        Returns:
            Cancellation result
        """
        try:
            body = {
                'instId': symbol,
                'ordId': order_id
            }
            
            data = self._request('POST', '/api/v5/trade/cancel-order', body=body)
            
            if not data:
                return {
                    'success': False,
                    'error': 'No cancel response'
                }
            
            result = data[0]
            
            return {
                'success': True,
                'order_id': result['ordId'],
                'status': result.get('sCode')
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to cancel order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_positions(self, inst_type: str = 'SWAP') -> List[Dict]:
        """
        Get open positions
        
        Args:
            inst_type: 'SWAP', 'FUTURES', 'MARGIN'
        
        Returns:
            List of positions
        """
        try:
            params = {
                'instType': inst_type
            }
            data = self._request('GET', '/api/v5/account/positions', params=params)
            
            positions = []
            for pos in data:
                position_amt = float(pos.get('pos', 0))
                if position_amt != 0:
                    positions.append({
                        'symbol': pos['instId'],
                        'size': abs(position_amt),
                        'side': 'Long' if position_amt > 0 else 'Short',
                        'entry_price': float(pos.get('avgPx', 0)),
                        'mark_price': float(pos.get('markPx', 0)),
                        'unrealized_pnl': float(pos.get('upl', 0)),
                        'leverage': int(float(pos.get('lever', 1)))
                    })
            
            return positions
        
        except Exception as e:
            LOG.error(f"❌ Failed to get positions: {e}")
            return []
    
    def close_position(self, symbol: str, inst_type: str = 'SWAP') -> Dict:
        """
        Close a position
        
        Args:
            symbol: Symbol to close
            inst_type: 'SWAP' or 'FUTURES'
        
        Returns:
            Close result
        """
        try:
            # Get current position
            positions = self.get_positions(inst_type=inst_type)
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not position:
                return {
                    'success': False,
                    'error': f'No open position for {symbol}'
                }
            
            # Close by placing opposite order
            side = 'sell' if position['side'] == 'Long' else 'buy'
            
            return self.place_order(
                symbol=symbol,
                side=side,
                order_type='market',
                quantity=position['size'],
                inst_type=inst_type,
                trade_mode='cross'
            )
        
        except Exception as e:
            LOG.error(f"❌ Failed to close position: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    connector = OKXConnector(demo=True)
    
    # Test connection
    print("Testing connection...")
    result = connector.test_connection()
    print(f"Connection: {result}")
    
    # Test ticker
    print("\nTesting ticker...")
    ticker = connector.get_ticker('BTC-USDT')
    print(f"BTC Price: ${ticker.get('last_price', 'N/A')}")
