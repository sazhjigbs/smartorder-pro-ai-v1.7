#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Paper Trading Engine v2
===========================================
Moteur de paper trading professionnel avec prix réels

Features:
- Ordres simulés (Market, Limit, Stop)
- Prix réels via API publiques (Binance, Bybit)
- Portfolio virtuel avec USDT
- Historique complet des trades
- Calcul PNL en temps réel
- Slippage simulation
- Fees simulation

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from enum import Enum

LOG = logging.getLogger("paper_trading")

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    """Ordre de trading"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: float
    average_price: float
    timestamp: str
    filled_timestamp: Optional[str]
    fees: float
    strategy: Optional[str]

@dataclass
class Position:
    """Position ouverte"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float
    side: str
    timestamp: str

@dataclass
class Trade:
    """Trade exécuté"""
    id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    fees: float
    timestamp: str
    strategy: Optional[str]

class PriceProvider:
    """Fournisseur de prix réels"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 5  # secondes
        
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Récupère le prix actuel d'un symbole
        
        Args:
            symbol: Trading pair (ex: BTCUSDT)
            
        Returns:
            Prix actuel ou None si erreur
        """
        # Check cache
        if symbol in self.cache:
            cached_price, cached_time = self.cache[symbol]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return cached_price
        
        # Fetch from Binance public API
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                self.cache[symbol] = (price, datetime.now())
                return price
        except:
            pass
        
        # Fallback to Bybit
        try:
            url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result') and data['result'].get('list'):
                    price = float(data['result']['list'][0]['lastPrice'])
                    self.cache[symbol] = (price, datetime.now())
                    return price
        except:
            pass
        
        return None
    
    def get_orderbook(self, symbol: str) -> Dict:
        """Récupère l'orderbook pour simulation d'exécution réaliste"""
        try:
            url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=20"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'bids': [(float(p), float(q)) for p, q in data['bids']],
                    'asks': [(float(p), float(q)) for p, q in data['asks']]
                }
        except:
            pass
        
        return {'bids': [], 'asks': []}

class PaperTradingEngine:
    """
    Moteur de Paper Trading
    
    Simule trading réel avec prix réels mais sans argent réel
    """
    
    def __init__(self, initial_balance: float = 10000.0, data_file: str = "/opt/smartorder-pro/data/paper_trading.json"):
        """
        Initialize Paper Trading Engine
        
        Args:
            initial_balance: Balance USDT initiale
            data_file: Fichier de sauvegarde
        """
        self.data_file = data_file
        self.price_provider = PriceProvider()
        
        # Load or initialize state
        self.state = self._load_state()
        
        if not self.state:
            self.state = {
                'balance': initial_balance,
                'initial_balance': initial_balance,
                'positions': {},
                'orders': {},
                'trades': [],
                'pnl_history': [],
                'created_at': datetime.now().isoformat()
            }
            self._save_state()
        
        LOG.info(f"✅ Paper Trading Engine initialized | Balance: {self.state['balance']:.2f} USDT")
    
    def _load_state(self) -> Optional[Dict]:
        """Charge l'état depuis le fichier"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _save_state(self):
        """Sauvegarde l'état"""
        import os
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None,
                   stop_price: Optional[float] = None,
                   strategy: Optional[str] = None) -> Dict:
        """
        Place un ordre
        
        Args:
            symbol: Trading pair
            side: 'buy' ou 'sell'
            order_type: 'market', 'limit', 'stop_market', 'stop_limit'
            quantity: Quantité
            price: Prix limite (pour limit orders)
            stop_price: Prix stop (pour stop orders)
            strategy: Nom de la stratégie
            
        Returns:
            Order result
        """
        try:
            # Validate
            if quantity <= 0:
                return {'success': False, 'error': 'Invalid quantity'}
            
            # Get current price
            current_price = self.price_provider.get_price(symbol)
            if not current_price:
                return {'success': False, 'error': 'Cannot fetch price'}
            
            # Create order ID
            order_id = f"PAPER_{datetime.now().timestamp()}"
            
            # Create order
            order = Order(
                id=order_id,
                symbol=symbol,
                side=OrderSide(side.lower()),
                type=OrderType(order_type.lower()),
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                status=OrderStatus.PENDING,
                filled_quantity=0.0,
                average_price=0.0,
                timestamp=datetime.now().isoformat(),
                filled_timestamp=None,
                fees=0.0,
                strategy=strategy
            )
            
            # Process order immediately for market orders
            if order.type == OrderType.MARKET:
                result = self._execute_market_order(order, current_price)
            else:
                # Add to pending orders
                self.state['orders'][order_id] = {
                    'id': order.id,
                    'symbol': order.symbol,
                    'side': order.side.value,
                    'type': order.type.value,
                    'quantity': order.quantity,
                    'price': order.price,
                    'stop_price': order.stop_price,
                    'status': order.status.value,
                    'filled_quantity': order.filled_quantity,
                    'average_price': order.average_price,
                    'timestamp': order.timestamp,
                    'filled_timestamp': order.filled_timestamp,
                    'fees': order.fees,
                    'strategy': order.strategy
                }
                self._save_state()
                result = {'success': True, 'order_id': order_id, 'status': 'pending'}
            
            return result
            
        except Exception as e:
            LOG.error(f"❌ Order failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_market_order(self, order: Order, current_price: float) -> Dict:
        """Exécute un ordre market"""
        # Calculate with slippage (0.05% default)
        slippage = 0.0005
        if order.side == OrderSide.BUY:
            execution_price = current_price * (1 + slippage)
        else:
            execution_price = current_price * (1 - slippage)
        
        # Calculate fees (0.1% default)
        fee_rate = 0.001
        cost = order.quantity * execution_price
        fees = cost * fee_rate
        
        # Check balance for buy orders
        if order.side == OrderSide.BUY:
            total_cost = cost + fees
            if total_cost > self.state['balance']:
                return {'success': False, 'error': 'Insufficient balance'}
            
            # Deduct from balance
            self.state['balance'] -= total_cost
            
            # Add to position
            self._add_to_position(order.symbol, order.quantity, execution_price, 'long')
            
        else:  # SELL
            # Check if we have the position
            if order.symbol not in self.state['positions']:
                return {'success': False, 'error': 'No position to sell'}
            
            position = self.state['positions'][order.symbol]
            if position['quantity'] < order.quantity:
                return {'success': False, 'error': 'Insufficient position quantity'}
            
            # Add to balance
            self.state['balance'] += (cost - fees)
            
            # Update position
            self._remove_from_position(order.symbol, order.quantity, execution_price)
        
        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_price = execution_price
        order.fees = fees
        order.filled_timestamp = datetime.now().isoformat()
        
        # Save order
        self.state['orders'][order.id] = {
            'id': order.id,
            'symbol': order.symbol,
            'side': order.side.value,
            'type': order.type.value,
            'quantity': order.quantity,
            'price': order.price,
            'stop_price': order.stop_price,
            'status': order.status.value,
            'filled_quantity': order.filled_quantity,
            'average_price': order.average_price,
            'timestamp': order.timestamp,
            'filled_timestamp': order.filled_timestamp,
            'fees': order.fees,
            'strategy': order.strategy
        }
        
        # Create trade
        trade = Trade(
            id=f"TRADE_{datetime.now().timestamp()}",
            order_id=order.id,
            symbol=order.symbol,
            side=order.side.value,
            quantity=order.quantity,
            price=execution_price,
            fees=fees,
            timestamp=datetime.now().isoformat(),
            strategy=order.strategy
        )
        self.state['trades'].append(asdict(trade))
        
        self._save_state()
        
        LOG.info(f"✅ Order executed: {order.side.value.upper()} {order.quantity} {order.symbol} @ {execution_price:.2f}")
        
        return {
            'success': True,
            'order_id': order.id,
            'status': 'filled',
            'price': execution_price,
            'fees': fees,
            'balance': self.state['balance']
        }
    
    def _add_to_position(self, symbol: str, quantity: float, price: float, side: str):
        """Ajoute à une position"""
        if symbol not in self.state['positions']:
            self.state['positions'][symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': price,
                'side': side,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Average price
            pos = self.state['positions'][symbol]
            total_qty = pos['quantity'] + quantity
            pos['entry_price'] = (pos['entry_price'] * pos['quantity'] + price * quantity) / total_qty
            pos['quantity'] = total_qty
    
    def _remove_from_position(self, symbol: str, quantity: float, exit_price: float):
        """Retire d'une position"""
        if symbol in self.state['positions']:
            pos = self.state['positions'][symbol]
            
            # Calculate PNL
            pnl = (exit_price - pos['entry_price']) * quantity
            
            # Update position
            pos['quantity'] -= quantity
            
            if pos['quantity'] <= 0:
                del self.state['positions'][symbol]
            
            # Add to PNL history
            self.state['pnl_history'].append({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'pnl': pnl,
                'exit_price': exit_price,
                'entry_price': pos['entry_price']
            })
    
    def get_balance(self) -> Dict:
        """Récupère le balance actuel"""
        total_value = self.state['balance']
        
        # Add position values
        for symbol, pos in self.state['positions'].items():
            current_price = self.price_provider.get_price(symbol)
            if current_price:
                total_value += pos['quantity'] * current_price
        
        pnl = total_value - self.state['initial_balance']
        pnl_percent = (pnl / self.state['initial_balance']) * 100
        
        return {
            'balance': self.state['balance'],
            'total_value': total_value,
            'initial_balance': self.state['initial_balance'],
            'pnl': pnl,
            'pnl_percent': pnl_percent
        }
    
    def get_positions(self) -> List[Dict]:
        """Récupère les positions ouvertes"""
        positions = []
        
        for symbol, pos in self.state['positions'].items():
            current_price = self.price_provider.get_price(symbol)
            if current_price:
                pnl = (current_price - pos['entry_price']) * pos['quantity']
                pnl_percent = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                
                positions.append({
                    'symbol': symbol,
                    'quantity': pos['quantity'],
                    'entry_price': pos['entry_price'],
                    'current_price': current_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'side': pos['side'],
                    'timestamp': pos['timestamp']
                })
        
        return positions
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Récupère les ordres"""
        orders = list(self.state['orders'].values())
        
        if status:
            orders = [o for o in orders if o['status'] == status]
        
        return orders
    
    def get_trades(self, limit: int = 50) -> List[Dict]:
        """Récupère l'historique des trades"""
        return self.state['trades'][-limit:]
    
    def get_pnl_history(self) -> List[Dict]:
        """Récupère l'historique PNL"""
        return self.state['pnl_history']
    
    def reset(self, initial_balance: Optional[float] = None):
        """Reset le paper trading"""
        if initial_balance:
            self.state['initial_balance'] = initial_balance
        
        self.state['balance'] = self.state['initial_balance']
        self.state['positions'] = {}
        self.state['orders'] = {}
        self.state['trades'] = []
        self.state['pnl_history'] = []
        self.state['created_at'] = datetime.now().isoformat()
        
        self._save_state()
        LOG.info("🔄 Paper Trading reset")


# Global instance
_engine = None

def get_paper_trading_engine() -> PaperTradingEngine:
    """Get global paper trading engine instance"""
    global _engine
    if _engine is None:
        _engine = PaperTradingEngine()
    return _engine


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    engine = PaperTradingEngine(initial_balance=1000.0)
    
    # Place market buy order
    result = engine.place_order(
        symbol='BTCUSDT',
        side='buy',
        order_type='market',
        quantity=0.01,
        strategy='Test'
    )
    print(f"Order result: {result}")
    
    # Get balance
    balance = engine.get_balance()
    print(f"Balance: {balance}")
    
    # Get positions
    positions = engine.get_positions()
    print(f"Positions: {positions}")
