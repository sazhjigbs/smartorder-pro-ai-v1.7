#!/usr/bin/env python3
"""
🔥 SAFELOGIC SmartOrder PRO - Unified Trading Manager
====================================================
Gestionnaire unifié de trading RÉEL avec multi-exchange
by MAIGA ABOUBACAR

Remplace l'ancien bybit_client.py avec un système professionnel

Features:
- Trading RÉEL sur Bybit (spot + futures)
- Multi-exchange ready (Binance, OKX, KuCoin)
- Retry automatique + rate limiting
- Cache intelligent
- Health monitoring
- Security intégré (encryption API keys)

Usage:
    from core.unified_trading_manager import UnifiedTradingManager
    
    manager = UnifiedTradingManager()
    
    # Get balance
    balance = manager.get_balance(exchange='bybit')
    
    # Place order
    order = manager.place_order(
        exchange='bybit',
        symbol='BTCUSDT',
        side='Buy',
        order_type='Market',
        quantity=0.001
    )
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

# Import connecteurs
sys.path.insert(0, str(Path(__file__).parent.parent))

from exchange_connectors.bybit_connector import BybitConnector
from exchange_connectors.binance_connector import BinanceConnector
from exchange_connectors.okx_connector import OKXConnector
from exchange_connectors.kucoin_connector import KuCoinConnector
from security.key_manager import SecurityManager
from monitoring.exchange_health_monitor import ExchangeHealthMonitor

LOG = logging.getLogger("unified_trading")
LOG.setLevel(logging.INFO)

# Windows-compatible logging
try:
    log_dir = "C:\\smartorder-pro\\logs"
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(f"{log_dir}\\unified_trading.log")
except:
    fh = logging.FileHandler("unified_trading.log")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
LOG.addHandler(fh)


class UnifiedTradingManager:
    """
    Gestionnaire unifié de trading multi-exchange
    
    Supporte:
    - Bybit (spot + futures)
    - Binance (spot + futures) ✅
    - OKX (spot + futures) ✅
    - KuCoin (spot + futures) ✅
    """
    
    def __init__(self, use_encryption: bool = True):
        """
        Initialize Unified Trading Manager
        
        Args:
            use_encryption: Utiliser encryption pour API keys (recommandé)
        """
        self.use_encryption = use_encryption
        
        # Security manager
        if use_encryption:
            self.security = SecurityManager()
        else:
            self.security = None
        
        # Health monitor
        self.health_monitor = ExchangeHealthMonitor()
        
        # Connecteurs actifs
        self.connectors = {}
        
        # Config
        self.config = self._load_config()
        
        # Initialize exchanges
        self._initialize_exchanges()
        
        LOG.info("✅ Unified Trading Manager initialized")
    
    def _load_config(self) -> Dict:
        """Charge configuration depuis .env et config/bot_config.json"""
        config = {
            'active_exchange': os.getenv('ACTIVE_EXCHANGE', 'bybit'),
            'paper_trading': os.getenv('PAPER_TRADING', 'false').lower() == 'true',
            'testnet': os.getenv('USE_TESTNET', 'false').lower() == 'true',
            'exchanges': {}
        }
        
        # Bybit config
        if self.use_encryption and self.security:
            # Load encrypted keys
            bybit_keys = self.security.get_api_keys('bybit')
            if bybit_keys:
                config['exchanges']['bybit'] = {
                    'enabled': True,
                    'api_key': bybit_keys['api_key'],
                    'api_secret': bybit_keys['api_secret'],
                    'testnet': config['testnet']
                }
        else:
            # Load from .env (plain text - not recommended for production)
            config['exchanges']['bybit'] = {
                'enabled': bool(os.getenv('BYBIT_API_KEY')),
                'api_key': os.getenv('BYBIT_API_KEY', ''),
                'api_secret': os.getenv('BYBIT_API_SECRET', ''),
                'testnet': config['testnet']
            }
        
        # Binance config
        if self.use_encryption and self.security:
            binance_keys = self.security.get_api_keys('binance')
            if binance_keys:
                config['exchanges']['binance'] = {
                    'enabled': True,
                    'api_key': binance_keys['api_key'],
                    'api_secret': binance_keys['api_secret'],
                    'testnet': config['testnet']
                }
        else:
            config['exchanges']['binance'] = {
                'enabled': bool(os.getenv('BINANCE_API_KEY')),
                'api_key': os.getenv('BINANCE_API_KEY', ''),
                'api_secret': os.getenv('BINANCE_API_SECRET', ''),
                'testnet': config['testnet']
            }
        
        # OKX config
        if self.use_encryption and self.security:
            okx_keys = self.security.get_api_keys('okx')
            if okx_keys:
                config['exchanges']['okx'] = {
                    'enabled': True,
                    'api_key': okx_keys['api_key'],
                    'api_secret': okx_keys['api_secret'],
                    'passphrase': okx_keys.get('passphrase', ''),
                    'demo': config['testnet']
                }
        else:
            config['exchanges']['okx'] = {
                'enabled': bool(os.getenv('OKX_API_KEY')),
                'api_key': os.getenv('OKX_API_KEY', ''),
                'api_secret': os.getenv('OKX_API_SECRET', ''),
                'passphrase': os.getenv('OKX_PASSPHRASE', ''),
                'demo': config['testnet']
            }
        
        # KuCoin config
        if self.use_encryption and self.security:
            kucoin_keys = self.security.get_api_keys('kucoin')
            if kucoin_keys:
                config['exchanges']['kucoin'] = {
                    'enabled': True,
                    'api_key': kucoin_keys['api_key'],
                    'api_secret': kucoin_keys['api_secret'],
                    'passphrase': kucoin_keys.get('passphrase', ''),
                    'sandbox': config['testnet']
                }
        else:
            config['exchanges']['kucoin'] = {
                'enabled': bool(os.getenv('KUCOIN_API_KEY')),
                'api_key': os.getenv('KUCOIN_API_KEY', ''),
                'api_secret': os.getenv('KUCOIN_API_SECRET', ''),
                'passphrase': os.getenv('KUCOIN_PASSPHRASE', ''),
                'sandbox': config['testnet']
            }
        
        return config
    
    def _initialize_exchanges(self):
        """Initialize exchange connectors"""
        # Bybit
        if self.config['exchanges']['bybit']['enabled']:
            try:
                self.connectors['bybit'] = BybitConnector(
                    api_key=self.config['exchanges']['bybit']['api_key'],
                    api_secret=self.config['exchanges']['bybit']['api_secret'],
                    testnet=self.config['exchanges']['bybit']['testnet']
                )
                LOG.info("✅ Bybit connector initialized")
            except Exception as e:
                LOG.error(f"❌ Failed to initialize Bybit: {e}")
        
        # Binance
        if self.config['exchanges'].get('binance', {}).get('enabled'):
            try:
                self.connectors['binance'] = BinanceConnector(
                    api_key=self.config['exchanges']['binance']['api_key'],
                    api_secret=self.config['exchanges']['binance']['api_secret'],
                    testnet=self.config['exchanges']['binance']['testnet']
                )
                LOG.info("✅ Binance connector initialized")
            except Exception as e:
                LOG.error(f"❌ Failed to initialize Binance: {e}")
        
        # OKX
        if self.config['exchanges'].get('okx', {}).get('enabled'):
            try:
                self.connectors['okx'] = OKXConnector(
                    api_key=self.config['exchanges']['okx']['api_key'],
                    api_secret=self.config['exchanges']['okx']['api_secret'],
                    passphrase=self.config['exchanges']['okx']['passphrase'],
                    demo=self.config['exchanges']['okx']['demo']
                )
                LOG.info("✅ OKX connector initialized")
            except Exception as e:
                LOG.error(f"❌ Failed to initialize OKX: {e}")
        
        # KuCoin
        if self.config['exchanges'].get('kucoin', {}).get('enabled'):
            try:
                self.connectors['kucoin'] = KuCoinConnector(
                    api_key=self.config['exchanges']['kucoin']['api_key'],
                    api_secret=self.config['exchanges']['kucoin']['api_secret'],
                    passphrase=self.config['exchanges']['kucoin']['passphrase'],
                    sandbox=self.config['exchanges']['kucoin']['sandbox']
                )
                LOG.info("✅ KuCoin connector initialized")
            except Exception as e:
                LOG.error(f"❌ Failed to initialize KuCoin: {e}")
    
    # ==================== BALANCE ====================
    
    def get_balance(self, exchange: str = 'bybit', account_type: str = 'UNIFIED') -> Dict:
        """
        Get wallet balance from exchange
        
        Args:
            exchange: 'bybit' | 'binance' | 'okx' | 'kucoin'
            account_type: 'UNIFIED' | 'SPOT' | 'CONTRACT'
        
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
        if exchange not in self.connectors:
            LOG.error(f"❌ Exchange {exchange} not initialized")
            return {}
        
        # Check health
        if not self.health_monitor.is_healthy(exchange):
            LOG.warning(f"⚠️ Exchange {exchange} is not healthy, skipping...")
            return {}
        
        try:
            connector = self.connectors[exchange]
            balance = connector.get_wallet_balance(account_type=account_type)
            
            LOG.info(f"✅ Balance retrieved from {exchange}: ${balance.get('total_equity', 0):.2f}")
            
            return balance
            
        except Exception as e:
            LOG.error(f"❌ Error getting balance from {exchange}: {e}")
            return {}
    
    # ==================== POSITIONS ====================
    
    def get_positions(self, exchange: str = 'bybit', category: str = 'linear') -> List[Dict]:
        """
        Get open positions from exchange
        
        Args:
            exchange: 'bybit' | 'binance' | 'okx' | 'kucoin'
            category: 'spot' | 'linear' | 'inverse'
        
        Returns:
            List of positions with details
        """
        if exchange not in self.connectors:
            LOG.error(f"❌ Exchange {exchange} not initialized")
            return []
        
        try:
            connector = self.connectors[exchange]
            positions = connector.get_positions(category=category)
            
            LOG.info(f"✅ {len(positions)} positions retrieved from {exchange}")
            
            return positions
            
        except Exception as e:
            LOG.error(f"❌ Error getting positions from {exchange}: {e}")
            return []
    
    # ==================== TRADING ====================
    
    def place_order(
        self,
        exchange: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        category: str = 'spot'
    ) -> Dict:
        """
        Place order on exchange
        
        Args:
            exchange: 'bybit' | 'binance' | 'okx' | 'kucoin'
            symbol: Trading pair (ex: 'BTCUSDT')
            side: 'Buy' | 'Sell'
            order_type: 'Market' | 'Limit'
            quantity: Order quantity
            price: Order price (required for Limit)
            category: 'spot' | 'linear' | 'inverse'
        
        Returns:
            Order result dict
        """
        # Check paper trading mode
        if self.config['paper_trading']:
            LOG.warning("⚠️ PAPER TRADING MODE - Order NOT executed on real exchange")
            return {
                'success': False,
                'message': 'Paper trading mode is enabled. Set PAPER_TRADING=false in .env to trade real.',
                'order': None
            }
        
        if exchange not in self.connectors:
            LOG.error(f"❌ Exchange {exchange} not initialized")
            return {'success': False, 'message': f'Exchange {exchange} not available'}
        
        # Check health
        if not self.health_monitor.is_healthy(exchange):
            LOG.error(f"❌ Exchange {exchange} is not healthy, order rejected")
            return {'success': False, 'message': f'Exchange {exchange} is down'}
        
        try:
            connector = self.connectors[exchange]
            
            # Place order
            order = connector.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                qty=quantity,  # Note: connector uses 'qty' not 'quantity'
                price=price,
                category=category
            )
            
            if order.get('success'):
                LOG.info(f"✅ Order placed on {exchange}: {side} {quantity} {symbol} @ {order_type}")
            else:
                LOG.error(f"❌ Order failed on {exchange}: {order.get('message')}")
            
            return order
            
        except Exception as e:
            LOG.error(f"❌ Error placing order on {exchange}: {e}")
            return {'success': False, 'message': str(e)}
    
    def close_position(
        self,
        exchange: str,
        symbol: str,
        category: str = 'linear'
    ) -> Dict:
        """
        Close position on exchange
        
        Args:
            exchange: 'bybit' | 'binance' | 'okx' | 'kucoin'
            symbol: Trading pair
            category: 'linear' | 'inverse'
        
        Returns:
            Result dict
        """
        if exchange not in self.connectors:
            return {'success': False, 'message': f'Exchange {exchange} not available'}
        
        try:
            connector = self.connectors[exchange]
            result = connector.close_position(symbol=symbol, category=category)
            
            LOG.info(f"✅ Position closed on {exchange}: {symbol}")
            
            return result
            
        except Exception as e:
            LOG.error(f"❌ Error closing position on {exchange}: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== MARKET DATA ====================
    
    def get_ticker(self, exchange: str, symbol: str) -> Dict:
        """Get current ticker price"""
        if exchange not in self.connectors:
            return {}
        
        try:
            connector = self.connectors[exchange]
            ticker = connector.get_ticker(symbol=symbol)
            return ticker
        except Exception as e:
            LOG.error(f"❌ Error getting ticker from {exchange}: {e}")
            return {}
    
    # ==================== UTILITIES ====================
    
    def get_active_exchanges(self) -> List[str]:
        """Get list of active exchanges"""
        return list(self.connectors.keys())
    
    def get_exchange_health(self, exchange: str) -> Dict:
        """Get health status of exchange"""
        return self.health_monitor.get_health_status(exchange)
    
    def set_paper_trading(self, enabled: bool):
        """Enable/disable paper trading mode"""
        self.config['paper_trading'] = enabled
        LOG.info(f"⚙️ Paper trading {'ENABLED' if enabled else 'DISABLED'}")
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return {
            'active_exchange': self.config['active_exchange'],
            'paper_trading': self.config['paper_trading'],
            'testnet': self.config['testnet'],
            'active_exchanges': self.get_active_exchanges()
        }


# ==================== COMPATIBILITY LAYER ====================
# Backwards compatibility with old bybit_client.py

def wallet_spot_balances() -> Dict[str, Any]:
    """Compatibility function for old code"""
    manager = UnifiedTradingManager()
    balance = manager.get_balance(exchange='bybit', account_type='UNIFIED')
    
    # Transform to old format
    result = []
    if balance and 'coins' in balance:
        for coin, data in balance['coins'].items():
            if data['balance'] > 0:
                result.append({
                    'asset': coin,
                    'free': str(data['available']),
                    'locked': str(data['balance'] - data['available'])
                })
    
    return {'spot': result if result else [{'asset': 'No balances', 'free': '0', 'locked': '0'}]}


def futures_positions() -> Dict[str, Any]:
    """Compatibility function for old code"""
    manager = UnifiedTradingManager()
    positions = manager.get_positions(exchange='bybit', category='linear')
    
    # Transform to old format
    result = []
    for pos in positions:
        if float(pos.get('size', 0)) > 0:
            result.append({
                'symbol': pos.get('symbol'),
                'side': pos.get('side'),
                'size': pos.get('size'),
                'entryPrice': pos.get('avgPrice'),
                'unrealPnl': pos.get('unrealisedPnl'),
                'leverage': pos.get('leverage'),
                'markPrice': pos.get('markPrice'),
                'liqPrice': pos.get('liqPrice'),
                'positionValue': pos.get('positionValue')
            })
    
    if not result:
        return {'futures': [{'symbol': 'Aucune position ouverte', 'side': '-', 'size': '0', 'entryPrice': '-', 'unrealPnl': '0', 'leverage': '-'}]}
    
    return {'futures': result}


def system_ping() -> Dict[str, Any]:
    """Compatibility function for old code"""
    manager = UnifiedTradingManager()
    health = manager.get_exchange_health('bybit')
    return {'ok': health.get('is_healthy', False), 'data': health}


# ==================== SINGLETON ====================

_manager_instance = None

def get_trading_manager() -> UnifiedTradingManager:
    """Get singleton instance of trading manager"""
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = UnifiedTradingManager()
    
    return _manager_instance


if __name__ == "__main__":
    print("🔥 Testing Unified Trading Manager...")
    
    manager = UnifiedTradingManager()
    
    print("\n📊 Config:")
    print(json.dumps(manager.get_config(), indent=2))
    
    print("\n💰 Getting balance...")
    balance = manager.get_balance(exchange='bybit')
    print(json.dumps(balance, indent=2))
    
    print("\n📍 Getting positions...")
    positions = manager.get_positions(exchange='bybit')
    print(f"Found {len(positions)} positions")
    
    print("\n✅ Test completed!")
