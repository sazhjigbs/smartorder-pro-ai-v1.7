"""
Binance Exchange Connector
Professional connector for Binance Spot & Futures trading

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

LOG = logging.getLogger(__name__)


class BinanceConnector:
    """
    Binance API Connector - Spot & Futures
    
    Features:
    - Spot trading
    - Futures USDT-M
    - Rate limiting (1200 req/min)
    - Auto retry on errors
    - Testnet support
    """
    
    def __init__(self, 
                 api_key: str = None, 
                 api_secret: str = None,
                 testnet: bool = False):
        """
        Initialize Binance connector
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default: False)
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.testnet = testnet
        
        # Endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision"
            self.futures_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://api.binance.com"
            self.futures_url = "https://fapi.binance.com"
        
        # Rate limiting
        self.max_requests_per_minute = 1200
        self.request_timestamps = []
        
        # Retry config
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        LOG.info(f"✅ Binance Connector initialized (testnet={testnet})")
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature for Binance API"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                   if now - ts < 60]
        
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_timestamps[0])
            LOG.warning(f"⚠️ Rate limit reached, sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    def _request(self, 
                 method: str, 
                 endpoint: str, 
                 params: Dict = None,
                 signed: bool = False,
                 futures: bool = False) -> Dict:
        """
        Make HTTP request to Binance API
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Require signature (default: False)
            futures: Use futures API (default: False)
        
        Returns:
            Response data
        """
        self._check_rate_limit()
        
        base_url = self.futures_url if futures else self.base_url
        url = f"{base_url}{endpoint}"
        
        params = params or {}
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, params=params, headers=headers, timeout=10)
                elif method == 'DELETE':
                    response = requests.delete(url, params=params, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                LOG.error(f"❌ Binance API error (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    def test_connection(self) -> Dict:
        """Test connectivity to Binance API"""
        try:
            # Test spot
            spot_status = self._request('GET', '/api/v3/ping')
            
            # Test futures
            futures_status = self._request('GET', '/fapi/v1/ping', futures=True)
            
            return {
                'success': True,
                'exchange': 'binance',
                'spot': spot_status is not None,
                'futures': futures_status is not None,
                'testnet': self.testnet
            }
        except Exception as e:
            LOG.error(f"❌ Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_balance(self, account_type: str = 'spot') -> Dict:
        """
        Get account balance
        
        Args:
            account_type: 'spot' or 'futures'
        
        Returns:
            Balance data
        """
        try:
            if account_type == 'spot':
                data = self._request('GET', '/api/v3/account', signed=True)
                balances = []
                total_equity = 0.0
                
                for balance in data.get('balances', []):
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    total = free + locked
                    
                    if total > 0:
                        balances.append({
                            'coin': balance['asset'],
                            'free': free,
                            'locked': locked,
                            'total': total
                        })
                        
                        # Rough USDT conversion (should use real prices)
                        if balance['asset'] in ['USDT', 'BUSD', 'USDC']:
                            total_equity += total
                
                return {
                    'success': True,
                    'account_type': 'spot',
                    'balances': balances,
                    'total_equity': total_equity
                }
            
            elif account_type == 'futures':
                data = self._request('GET', '/fapi/v2/account', signed=True, futures=True)
                
                return {
                    'success': True,
                    'account_type': 'futures',
                    'total_equity': float(data.get('totalWalletBalance', 0)),
                    'available_balance': float(data.get('availableBalance', 0)),
                    'total_unrealized_pnl': float(data.get('totalUnrealizedProfit', 0)),
                    'balances': data.get('assets', [])
                }
            
            else:
                raise ValueError(f"Invalid account_type: {account_type}")
        
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
            symbol: Trading pair (e.g., 'BTCUSDT')
        
        Returns:
            Ticker data
        """
        try:
            data = self._request('GET', '/api/v3/ticker/24hr', params={'symbol': symbol})
            
            return {
                'success': True,
                'symbol': symbol,
                'last_price': float(data['lastPrice']),
                'bid_price': float(data['bidPrice']),
                'ask_price': float(data['askPrice']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume_24h': float(data['volume']),
                'price_change_percent': float(data['priceChangePercent'])
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
                    account_type: str = 'spot',
                    time_in_force: str = 'GTC') -> Dict:
        """
        Place an order
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            order_type: 'MARKET' or 'LIMIT'
            quantity: Order quantity
            price: Limit price (required for LIMIT orders)
            account_type: 'spot' or 'futures'
            time_in_force: 'GTC', 'IOC', 'FOK'
        
        Returns:
            Order result
        """
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': quantity
            }
            
            if order_type.upper() == 'LIMIT':
                if not price:
                    raise ValueError("Price required for LIMIT orders")
                params['price'] = price
                params['timeInForce'] = time_in_force
            
            if account_type == 'spot':
                endpoint = '/api/v3/order'
                futures = False
            elif account_type == 'futures':
                endpoint = '/fapi/v1/order'
                futures = True
            else:
                raise ValueError(f"Invalid account_type: {account_type}")
            
            data = self._request('POST', endpoint, params=params, signed=True, futures=futures)
            
            return {
                'success': True,
                'order_id': data['orderId'],
                'symbol': data['symbol'],
                'side': data['side'],
                'type': data['type'],
                'quantity': float(data['origQty']),
                'price': float(data.get('price', 0)),
                'status': data['status']
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to place order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self,
                     symbol: str,
                     order_id: str,
                     account_type: str = 'spot') -> Dict:
        """
        Cancel an order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            account_type: 'spot' or 'futures'
        
        Returns:
            Cancellation result
        """
        try:
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            
            if account_type == 'spot':
                endpoint = '/api/v3/order'
                futures = False
            else:
                endpoint = '/fapi/v1/order'
                futures = True
            
            data = self._request('DELETE', endpoint, params=params, signed=True, futures=futures)
            
            return {
                'success': True,
                'order_id': data['orderId'],
                'status': data['status']
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
            data = self._request('GET', '/fapi/v2/positionRisk', signed=True, futures=True)
            
            positions = []
            for pos in data:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:  # Only active positions
                    positions.append({
                        'symbol': pos['symbol'],
                        'size': abs(position_amt),
                        'side': 'Long' if position_amt > 0 else 'Short',
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'leverage': int(pos['leverage'])
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
            
            # Close by placing opposite order
            side = 'SELL' if position['side'] == 'Long' else 'BUY'
            
            return self.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=position['size'],
                account_type='futures'
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
    
    connector = BinanceConnector(testnet=True)
    
    # Test connection
    print("Testing connection...")
    result = connector.test_connection()
    print(f"Connection: {result}")
    
    # Test ticker
    print("\nTesting ticker...")
    ticker = connector.get_ticker('BTCUSDT')
    print(f"BTC Price: ${ticker.get('last_price', 'N/A')}")
