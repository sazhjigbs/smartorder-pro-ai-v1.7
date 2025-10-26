# 🔧 MODULE TECHNIQUE MULTI-EXCHANGE - SmartOrder PRO

**Date :** 25 Octobre 2025  
**Objectif :** Compatibilité totale Bybit/Binance/KuCoin + Gestion intelligente

---

## 💡 PROBLÈMES À RÉSOUDRE

### 1. Bybit Unified Wallet
**Problème :** Un seul wallet unifié pour Spot + Futures  
**Solution :** Gestion intelligente du capital partagé

### 2. Fees différents par exchange
**Problème :** Chaque exchange a ses propres frais  
**Solution :** Cache dynamique + calcul ROI net

### 3. Minimum Order Size
**Problème :** Chaque paire a un minimum différent  
**Solution :** Validation pré-ordre + ajustement auto

### 4. Rate Limits
**Problème :** Limite d'ordres par seconde  
**Solution :** Queue intelligente + throttling adaptatif

### 5. Capital Management
**Problème :** Éviter surexposition  
**Solution :** Calcul exposition temps réel multi-exchange

---

## 🎯 MODULE 1 : UNIFIED WALLET MANAGER (Bybit)

### Problème Bybit Unified Wallet

```python
# Bybit V5 : Un seul wallet pour tout
{
    "accountType": "UNIFIED",
    "totalEquity": "10000 USDT",
    "availableBalance": "8500 USDT",
    # Ce capital est partagé entre:
    # - Spot trading
    # - Futures positions (avec leverage)
    # - Orders en attente
}
```

### Solution : Smart Capital Allocator

```python
class BybitUnifiedWalletManager:
    def __init__(self):
        self.total_equity = 0
        self.available_balance = 0
        self.spot_exposure = 0
        self.futures_exposure = 0  # Avec leverage
        self.orders_locked = 0
        
    def get_available_for_spot(self):
        """Calcule capital dispo pour spot"""
        # Reserve pour futures (marge)
        futures_reserved = self.calculate_futures_margin_required()
        
        # Reserve pour orders en attente
        orders_reserved = self.get_pending_orders_locked()
        
        # Dispo pour spot
        available_spot = (
            self.available_balance 
            - futures_reserved 
            - orders_reserved
            - self.get_safety_buffer()
        )
        
        return max(0, available_spot)
    
    def get_available_for_futures(self):
        """Calcule capital dispo pour futures"""
        # Considère exposition spot actuelle
        spot_locked = self.spot_exposure
        
        # Reserve sécurité
        safety = self.get_safety_buffer()
        
        # Dispo pour futures (peut utiliser leverage)
        available_futures = (
            self.available_balance 
            - spot_locked 
            - safety
        )
        
        return max(0, available_futures)
    
    def calculate_futures_margin_required(self):
        """Calcule marge requise pour futures"""
        total_margin = 0
        
        for position in self.get_futures_positions():
            # Initial Margin + Maintenance Margin
            im = position.quantity * position.price / position.leverage
            mm = im * 0.5  # 50% de IM
            
            total_margin += (im + mm)
        
        return total_margin
    
    def get_safety_buffer(self):
        """Buffer sécurité (5% du capital)"""
        return self.total_equity * 0.05
    
    def can_open_spot_order(self, amount_usdt):
        """Vérifie si peut ouvrir ordre spot"""
        available = self.get_available_for_spot()
        return amount_usdt <= available
    
    def can_open_futures_position(self, amount_usdt, leverage):
        """Vérifie si peut ouvrir position futures"""
        available = self.get_available_for_futures()
        margin_required = amount_usdt / leverage
        
        return margin_required <= available
```

---

## 🎯 MODULE 2 : FEES & LIMITS MANAGER

### Base de données Fees par Exchange

```python
EXCHANGE_FEES = {
    "bybit": {
        "spot": {
            "maker": 0.001,  # 0.1%
            "taker": 0.001   # 0.1%
        },
        "futures": {
            "maker": 0.0002,  # 0.02%
            "taker": 0.0006   # 0.06%
        }
    },
    "binance": {
        "spot": {
            "maker": 0.001,   # 0.1%
            "taker": 0.001    # 0.1%
        },
        "futures": {
            "maker": 0.0002,  # 0.02%
            "taker": 0.0004   # 0.04%
        }
    },
    "kucoin": {
        "spot": {
            "maker": 0.001,   # 0.1%
            "taker": 0.001    # 0.1%
        },
        "futures": {
            "maker": 0.0002,  # 0.02%
            "taker": 0.0006   # 0.06%
        }
    }
}
```

### Minimum Order Size Manager

```python
class MinOrderSizeManager:
    def __init__(self):
        self.limits_cache = {}
        self.last_update = {}
        
    def fetch_limits(self, exchange, symbol):
        """Récupère limites depuis exchange"""
        if exchange == "bybit":
            return self.fetch_bybit_limits(symbol)
        elif exchange == "binance":
            return self.fetch_binance_limits(symbol)
        elif exchange == "kucoin":
            return self.fetch_kucoin_limits(symbol)
    
    def fetch_bybit_limits(self, symbol):
        """Bybit V5 /v5/market/instruments-info"""
        info = bybit_client.get_instruments_info(
            category="spot",  # ou "linear" pour futures
            symbol=symbol
        )
        
        return {
            "minOrderQty": float(info['minOrderQty']),
            "maxOrderQty": float(info['maxOrderQty']),
            "minOrderAmt": float(info['minOrderAmt']),  # USDT
            "qtyStep": float(info['lotSizeFilter']['qtyStep']),
            "priceFilter": float(info['priceFilter']['tickSize'])
        }
    
    def validate_order_size(self, exchange, symbol, quantity, price):
        """Valide taille ordre"""
        limits = self.get_cached_limits(exchange, symbol)
        
        # 1. Check quantity
        if quantity < limits['minOrderQty']:
            raise ValueError(f"Quantity {quantity} < min {limits['minOrderQty']}")
        
        if quantity > limits['maxOrderQty']:
            raise ValueError(f"Quantity {quantity} > max {limits['maxOrderQty']}")
        
        # 2. Check notional (value in USDT)
        notional = quantity * price
        if notional < limits['minOrderAmt']:
            raise ValueError(f"Notional {notional} < min {limits['minOrderAmt']}")
        
        # 3. Check step size
        qty_step = limits['qtyStep']
        if (quantity % qty_step) != 0:
            # Auto-adjust to step
            quantity = self.round_to_step(quantity, qty_step)
        
        return True, quantity
    
    def round_to_step(self, value, step):
        """Arrondit selon step size"""
        precision = len(str(step).split('.')[-1])
        return round(value // step * step, precision)
    
    def adjust_quantity_to_min(self, exchange, symbol, quantity, price):
        """Ajuste quantité au minimum requis"""
        limits = self.get_cached_limits(exchange, symbol)
        
        # Si trop petit, ajuste au minimum
        if quantity < limits['minOrderQty']:
            quantity = limits['minOrderQty']
        
        # Vérifie notional
        notional = quantity * price
        if notional < limits['minOrderAmt']:
            # Calcule quantité pour atteindre min notional
            quantity = limits['minOrderAmt'] / price
            quantity = self.round_to_step(quantity, limits['qtyStep'])
        
        return quantity
```

---

## 🎯 MODULE 3 : RATE LIMIT MANAGER

### Rate Limits par Exchange

```python
RATE_LIMITS = {
    "bybit": {
        "spot": {
            "orders_per_second": 10,
            "orders_per_minute": 120,
            "weight_per_minute": 600
        },
        "futures": {
            "orders_per_second": 10,
            "orders_per_minute": 120,
            "weight_per_minute": 600
        }
    },
    "binance": {
        "spot": {
            "orders_per_second": 10,
            "orders_per_10sec": 100,
            "weight_per_minute": 1200
        },
        "futures": {
            "orders_per_second": 20,
            "orders_per_minute": 300,
            "weight_per_minute": 2400
        }
    },
    "kucoin": {
        "spot": {
            "orders_per_second": 10,
            "orders_per_minute": 200
        },
        "futures": {
            "orders_per_second": 10,
            "orders_per_minute": 200
        }
    }
}
```

### Intelligent Queue System

```python
from collections import deque
from datetime import datetime, timedelta
import asyncio

class SmartRateLimiter:
    def __init__(self, exchange, market_type):
        self.exchange = exchange
        self.market_type = market_type
        self.limits = RATE_LIMITS[exchange][market_type]
        
        # Queues par période
        self.orders_last_second = deque()
        self.orders_last_minute = deque()
        
        # Pending orders
        self.pending_queue = deque()
        
    async def can_send_order(self):
        """Vérifie si peut envoyer ordre maintenant"""
        now = datetime.now()
        
        # Clean old entries
        self.clean_old_entries(now)
        
        # Check limits
        if len(self.orders_last_second) >= self.limits['orders_per_second']:
            return False
            
        if len(self.orders_last_minute) >= self.limits['orders_per_minute']:
            return False
        
        return True
    
    async def wait_and_send(self, order_func, *args, **kwargs):
        """Attend disponibilité et envoie ordre"""
        while not await self.can_send_order():
            await asyncio.sleep(0.1)  # Wait 100ms
        
        # Send order
        result = await order_func(*args, **kwargs)
        
        # Record
        now = datetime.now()
        self.orders_last_second.append(now)
        self.orders_last_minute.append(now)
        
        return result
    
    def clean_old_entries(self, now):
        """Supprime entrées expirées"""
        one_second_ago = now - timedelta(seconds=1)
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean second queue
        while self.orders_last_second and self.orders_last_second[0] < one_second_ago:
            self.orders_last_second.popleft()
        
        # Clean minute queue
        while self.orders_last_minute and self.orders_last_minute[0] < one_minute_ago:
            self.orders_last_minute.popleft()
    
    async def batch_send_orders(self, orders_list):
        """Envoie plusieurs ordres avec throttling"""
        results = []
        
        for order in orders_list:
            result = await self.wait_and_send(
                order['func'],
                *order['args'],
                **order['kwargs']
            )
            results.append(result)
            
        return results
```

---

## 🎯 MODULE 4 : CAPITAL EXPOSURE MANAGER

### Calcul Exposition Multi-Exchange

```python
class GlobalExposureManager:
    def __init__(self):
        self.exchanges = {}  # bybit, binance, kucoin
        
    def calculate_total_exposure(self):
        """Calcule exposition totale"""
        total_equity = 0
        total_spot_exposure = 0
        total_futures_exposure = 0
        
        for exchange_name, exchange in self.exchanges.items():
            # Equity
            total_equity += exchange.get_total_equity()
            
            # Spot exposure
            for position in exchange.get_spot_positions():
                total_spot_exposure += position.value_usdt
            
            # Futures exposure (avec leverage)
            for position in exchange.get_futures_positions():
                # Exposition = quantity * price (pas la marge)
                exposure = position.quantity * position.price
                total_futures_exposure += exposure
        
        return {
            "total_equity": total_equity,
            "spot_exposure": total_spot_exposure,
            "futures_exposure": total_futures_exposure,
            "total_exposure": total_spot_exposure + total_futures_exposure,
            "exposure_ratio": (total_spot_exposure + total_futures_exposure) / total_equity
        }
    
    def can_open_new_position(self, amount_usdt, leverage=1):
        """Vérifie si peut ouvrir nouvelle position"""
        exposure = self.calculate_total_exposure()
        
        # Limite exposition à 80% du capital total
        max_exposure = exposure['total_equity'] * 0.80
        
        new_exposure = exposure['total_exposure'] + (amount_usdt * leverage)
        
        if new_exposure > max_exposure:
            return False, f"Max exposure {max_exposure} USDT atteint"
        
        return True, "OK"
    
    def get_available_capital(self):
        """Capital disponible global"""
        exposure = self.calculate_total_exposure()
        
        max_exposure = exposure['total_equity'] * 0.80
        current_exposure = exposure['total_exposure']
        
        available = max_exposure - current_exposure
        
        return max(0, available)
    
    def suggest_position_size(self, risk_pct=2, leverage=1):
        """Suggère taille position selon risque"""
        exposure = self.calculate_total_exposure()
        
        # Taille max selon risque (ex: 2% du capital)
        max_size = exposure['total_equity'] * (risk_pct / 100)
        
        # Ajuste selon capital disponible
        available = self.get_available_capital()
        
        # Prend le plus petit
        suggested_size = min(max_size, available / leverage)
        
        return suggested_size
```

---

## 🎯 MODULE 5 : SMART ORDER ROUTER

### Choix Exchange Optimal

```python
class SmartExchangeRouter:
    def __init__(self):
        self.exchanges = ['bybit', 'binance', 'kucoin']
        self.fees_manager = FeesManager()
        self.limits_manager = MinOrderSizeManager()
        
    def choose_best_exchange(self, symbol, quantity, price, order_type):
        """Choisit meilleur exchange"""
        scores = {}
        
        for exchange in self.exchanges:
            score = self.calculate_exchange_score(
                exchange, symbol, quantity, price, order_type
            )
            scores[exchange] = score
        
        # Trie par score
        best = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return best[0][0]  # Meilleur exchange
    
    def calculate_exchange_score(self, exchange, symbol, quantity, price, order_type):
        """Calcule score exchange"""
        score = 100
        
        # 1. Fees (important)
        fees = self.fees_manager.get_fees(exchange, order_type)
        fee_cost = quantity * price * fees['taker']
        score -= (fee_cost / (quantity * price)) * 100  # Pénalité fees
        
        # 2. Available balance
        balance = self.get_available_balance(exchange)
        if balance < (quantity * price):
            return 0  # Pas assez de capital
        
        # 3. Liquidity (spread)
        spread = self.get_current_spread(exchange, symbol)
        score -= spread * 100  # Pénalité spread
        
        # 4. Latency
        latency = self.get_average_latency(exchange)
        score -= latency / 10  # Pénalité latence
        
        # 5. Rate limit availability
        rate_limit_free = self.check_rate_limit_available(exchange)
        if not rate_limit_free:
            score -= 20
        
        return score
```

---

## 🎯 MODULE 6 : OPTIMISATIONS AVANCÉES

### 1. Order Batching (Regroupement)

```python
class OrderBatcher:
    def __init__(self):
        self.pending_orders = []
        self.batch_interval = 0.5  # 500ms
        
    async def add_order(self, order):
        """Ajoute ordre au batch"""
        self.pending_orders.append(order)
        
        # Si premier ordre, lance timer
        if len(self.pending_orders) == 1:
            asyncio.create_task(self.process_batch())
    
    async def process_batch(self):
        """Traite batch après délai"""
        await asyncio.sleep(self.batch_interval)
        
        if not self.pending_orders:
            return
        
        # Groupe par exchange
        by_exchange = {}
        for order in self.pending_orders:
            exchange = order['exchange']
            if exchange not in by_exchange:
                by_exchange[exchange] = []
            by_exchange[exchange].append(order)
        
        # Envoie par exchange
        for exchange, orders in by_exchange.items():
            await self.send_batch_to_exchange(exchange, orders)
        
        self.pending_orders.clear()
```

### 2. Smart Retry avec Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class SmartOrderExecutor:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def place_order_with_retry(self, exchange, order):
        """Place ordre avec retry intelligent"""
        try:
            result = await exchange.place_order(order)
            return result
            
        except InsufficientBalanceError:
            # Pas de retry si balance insuffisante
            raise
            
        except RateLimitError:
            # Wait plus longtemps
            await asyncio.sleep(5)
            raise  # Retry
            
        except NetworkError:
            # Retry immédiat
            raise
            
        except InvalidOrderError as e:
            # Tente ajustement
            if "minNotional" in str(e):
                order = self.adjust_to_min_notional(order)
                return await exchange.place_order(order)
            raise
```

### 3. Fallback Automatique

```python
class FallbackOrderSystem:
    def __init__(self):
        self.primary_exchange = "bybit"
        self.fallback_exchanges = ["binance", "kucoin"]
        
    async def execute_with_fallback(self, order):
        """Exécute avec fallback auto"""
        # Essaie primary
        try:
            return await self.execute_on_exchange(
                self.primary_exchange, order
            )
        except Exception as e:
            log(f"Primary exchange failed: {e}")
            
        # Essaie fallbacks
        for exchange in self.fallback_exchanges:
            try:
                log(f"Trying fallback: {exchange}")
                return await self.execute_on_exchange(exchange, order)
            except Exception as e:
                log(f"Fallback {exchange} failed: {e}")
                continue
        
        # Tous ont échoué
        raise AllExchangesFailedError("No exchange available")
```

### 4. Fee Optimization (Maker vs Taker)

```python
class FeeOptimizer:
    def decide_order_type(self, urgency, fee_diff):
        """Décide entre Maker (limit) ou Taker (market)"""
        # Urgency: 0-10 (0=pas urgent, 10=très urgent)
        
        if urgency >= 8:
            # Très urgent → Market (taker)
            return "MARKET"
        
        # Calcul économie fees
        savings = fee_diff  # Différence maker/taker
        
        if urgency <= 3 and savings > 0.0004:  # >0.04%
            # Pas urgent + économie significative → Limit (maker)
            return "LIMIT"
        
        # Cas moyen → Market IOC (immediate or cancel)
        return "MARKET_IOC"
    
    def place_maker_order(self, symbol, side, quantity, price):
        """Place ordre maker (limit)"""
        # Place légèrement mieux que prix actuel
        if side == "BUY":
            limit_price = price * 0.9999  # -0.01%
        else:  # SELL
            limit_price = price * 1.0001  # +0.01%
        
        return {
            "type": "LIMIT",
            "side": side,
            "quantity": quantity,
            "price": limit_price,
            "timeInForce": "POST_ONLY"  # Garantit maker
        }
```

### 5. Slippage Protection

```python
class SlippageProtector:
    def calculate_expected_slippage(self, symbol, quantity, side):
        """Calcule slippage attendu"""
        orderbook = self.get_orderbook(symbol)
        
        total_qty = 0
        total_cost = 0
        
        # Simule exécution dans orderbook
        levels = orderbook['asks'] if side == "BUY" else orderbook['bids']
        
        for price, qty in levels:
            if total_qty >= quantity:
                break
            
            qty_to_take = min(qty, quantity - total_qty)
            total_cost += qty_to_take * price
            total_qty += qty_to_take
        
        avg_price = total_cost / total_qty if total_qty > 0 else 0
        market_price = levels[0][0]
        
        slippage = abs(avg_price - market_price) / market_price
        
        return slippage
    
    def should_split_order(self, slippage, threshold=0.003):
        """Décide si doit split ordre"""
        return slippage > threshold  # >0.3%
    
    def split_large_order(self, quantity, num_chunks=5):
        """Split ordre en plusieurs parties"""
        chunk_size = quantity / num_chunks
        
        chunks = []
        for i in range(num_chunks):
            chunks.append({
                "quantity": chunk_size,
                "delay": i * 2  # 2 secondes entre chaque
            })
        
        return chunks
```

---

## 📦 LIBRAIRIES OPEN SOURCE RECOMMANDÉES

### 1. CCXT - Multi-Exchange
**Repo :** https://github.com/ccxt/ccxt

**Utilisation :**
```python
import ccxt

# Unified API pour tous exchanges
bybit = ccxt.bybit({'apiKey': '...', 'secret': '...'})
binance = ccxt.binance({'apiKey': '...', 'secret': '...'})
kucoin = ccxt.kucoin({'apiKey': '...', 'secret': '...'})

# Fetch limits
limits = bybit.fetch_trading_limits('BTC/USDT')
# {'min': 0.001, 'max': 1000, 'minNotional': 10}

# Fetch fees
fees = bybit.fetch_trading_fees()
```

**Avantages :**
- API unifiée
- Gère rate limits automatiquement
- Cache built-in
- 100+ exchanges supportés

---

### 2. PyBit - Bybit Spécialisé
**Repo :** https://github.com/bybit-exchange/pybit

**Utilisation :**
```python
from pybit.unified_trading import HTTP

client = HTTP(
    api_key="...",
    api_secret="..."
)

# Unified Wallet Balance
wallet = client.get_wallet_balance(accountType="UNIFIED")
```

**Pour Bybit Unified Wallet :**
- Gère wallet unifié correctement
- API V5 native
- WebSocket support

---

### 3. Tenacity - Smart Retry
**Repo :** https://github.com/jd/tenacity

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def place_order():
    ...
```

---

## ⚙️ CONFIGURATION .env

```bash
# Exchanges
EXCHANGES_ENABLED=bybit,binance,kucoin
PRIMARY_EXCHANGE=bybit

# Bybit
BYBIT_API_KEY=...
BYBIT_API_SECRET=...
BYBIT_UNIFIED_WALLET=true

# Binance
BINANCE_API_KEY=...
BINANCE_API_SECRET=...

# KuCoin
KUCOIN_API_KEY=...
KUCOIN_API_SECRET=...
KUCOIN_API_PASSPHRASE=...

# Limits
MAX_EXPOSURE_PCT=80          # 80% capital max
SAFETY_BUFFER_PCT=5          # 5% buffer sécurité
MAX_POSITIONS_TOTAL=20       # Max 20 positions tous exchanges

# Fees Optimization
PREFER_MAKER_ORDERS=true     # Préfère limit (maker)
MAX_SLIPPAGE_PCT=0.3         # 0.3% slippage max

# Rate Limits
ENABLE_RATE_LIMIT_QUEUE=true
BATCH_ORDERS_ENABLED=true
BATCH_INTERVAL_MS=500

# Fallback
ENABLE_AUTO_FALLBACK=true
FALLBACK_ORDER=binance,kucoin
```

---

## 🎯 ROADMAP DÉVELOPPEMENT

### Phase 1 (Semaine 1)
- [ ] Bybit Unified Wallet Manager
- [ ] Fees & Limits Cache
- [ ] Min Order Size Validator

### Phase 2 (Semaine 2)
- [ ] Rate Limit Manager
- [ ] Global Exposure Manager
- [ ] Smart Exchange Router

### Phase 3 (Semaine 3)
- [ ] Order Batching
- [ ] Smart Retry Logic
- [ ] Fallback System

### Phase 4 (Semaine 4)
- [ ] Fee Optimizer
- [ ] Slippage Protection
- [ ] Integration Tests

**Temps total : 1 mois (~160h)**

---

**Document créé le :** 25 Octobre 2025, 23:55 UTC  
**Module :** Multi-Exchange Technical  
**Objectif :** Compatibilité totale + Optimisations avancées 🔧
