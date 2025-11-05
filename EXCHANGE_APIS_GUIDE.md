# 📚 Guide APIs Exchange - Wallets Multi-Exchanges

## 🎯 Objectif

Unifier les appels aux wallets Binance, Bybit, OKX, KuCoin via une interface commune.

---

## 🔧 Option 1: CCXT (Recommandé pour commencer)

**Avantages:**
- ✅ Une seule bibliothèque pour 4 exchanges
- ✅ API unifiée (même code pour tous)
- ✅ Maintenance active (100k+ stars GitHub)
- ✅ Support Spot + Futures

**Installation:**

```bash
pip install ccxt
```

**Usage (`/opt/smartorder-pro/api/exchanges/ccxt_wallet.py`):**

```python
import ccxt
import os

class CCXTWallet:
    def __init__(self, exchange_name: str):
        """
        exchange_name: 'binance', 'bybit', 'okx', 'kucoin'
        """
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'apiKey': os.getenv(f'{exchange_name.upper()}_API_KEY'),
            'secret': os.getenv(f'{exchange_name.upper()}_SECRET'),
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}  # 'spot' ou 'future'
        })
    
    def get_balance(self):
        """Récupère tous les balances (Spot + Futures unifiés)"""
        return self.exchange.fetch_balance()
    
    def get_positions(self):
        """Récupère positions futures ouvertes"""
        return self.exchange.fetch_positions()
    
    def get_total_equity(self):
        """Calcule total equity (Spot + Futures)"""
        balance = self.get_balance()
        return balance.get('total', {}).get('USDT', 0)

# Usage FastAPI endpoint
from fastapi import APIRouter
router = APIRouter()

@router.get("/wallet/unified")
async def get_wallet_unified():
    # Utiliser l'exchange configuré (ex: Bybit)
    wallet = CCXTWallet('bybit')
    
    balance = wallet.get_balance()
    positions = wallet.get_positions()
    
    return {
        "total_equity": wallet.get_total_equity(),
        "available_balance": balance['free'].get('USDT', 0),
        "margin_used": balance['used'].get('USDT', 0),
        "positions": positions,
        "pnl_total": sum(p.get('unrealizedPnl', 0) for p in positions)
    }
```

**Références:**
- GitHub: https://github.com/ccxt/ccxt
- Docs: https://docs.ccxt.com/

---

## 🚀 Option 2: SDKs Officiels (Pour fonctionnalités avancées)

### **Binance**

```bash
pip install python-binance
```

**Unified Trading Account:**

```python
from binance.client import Client

client = Client(api_key=os.getenv('BINANCE_API_KEY'),
                api_secret=os.getenv('BINANCE_SECRET'))

# Balance Spot
spot_balance = client.get_account()

# Balance Futures USDT-M
futures_balance = client.futures_account_balance()

# Positions Futures
positions = client.futures_position_information()
```

**Docs:** https://python-binance.readthedocs.io/

---

### **Bybit - Unified Trading Account (UTA)**

```bash
pip install pybit
```

**UTA (Spot + Futures + Options unifiés):**

```python
from pybit.unified_trading import HTTP

session = HTTP(
    testnet=False,
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_SECRET')
)

# Wallet Balance (UTA unifié)
wallet = session.get_wallet_balance(accountType="UNIFIED")

# Positions
positions = session.get_positions(category="linear", settleCoin="USDT")

# Account Info
account = session.get_account_info()
```

**Docs:** 
- PyBit: https://github.com/bybit-exchange/pybit
- Bybit API: https://bybit-exchange.github.io/docs/v5/intro

---

### **OKX**

```bash
pip install okx
```

**Trading Account:**

```python
import okx.Account as Account
import okx.MarketData as Market

accountAPI = Account.AccountAPI(
    api_key=os.getenv('OKX_API_KEY'),
    api_secret_key=os.getenv('OKX_SECRET'),
    passphrase=os.getenv('OKX_PASSPHRASE'),
    flag='0'  # 0: production, 1: testnet
)

# Balance
balance = accountAPI.get_account_balance()

# Positions
positions = accountAPI.get_positions(instType="SWAP")  # SWAP = perpetual futures
```

**Docs:** https://www.okx.com/docs-v5/en/

---

### **KuCoin**

```bash
pip install python-kucoin
```

**Spot + Futures:**

```python
from kucoin.client import Client

client = Client(
    api_key=os.getenv('KUCOIN_API_KEY'),
    api_secret=os.getenv('KUCOIN_SECRET'),
    api_passphrase=os.getenv('KUCOIN_PASSPHRASE')
)

# Spot Balance
spot_accounts = client.get_accounts()

# Futures Balance
futures_client = client.futures
futures_balance = futures_client.get_account_overview()

# Positions
positions = futures_client.get_all_position()
```

**Docs:** https://python-kucoin.readthedocs.io/

---

## 🏗️ Architecture Recommandée

**Structure backend (`/opt/smartorder-pro/api/exchanges/`):**

```
exchanges/
├── __init__.py
├── base.py              # Interface abstraite
├── ccxt_wallet.py       # Implémentation CCXT (défaut)
├── binance_wallet.py    # SDK Binance (si besoin spécifique)
├── bybit_wallet.py      # SDK Bybit UTA
├── okx_wallet.py        # SDK OKX
└── kucoin_wallet.py     # SDK KuCoin
```

**Interface abstraite (`base.py`):**

```python
from abc import ABC, abstractmethod
from typing import Dict, List

class BaseWallet(ABC):
    @abstractmethod
    def get_balance(self) -> Dict:
        """Retourne balance unified"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """Retourne positions futures ouvertes"""
        pass
    
    @abstractmethod
    def get_pnl(self) -> float:
        """Retourne PnL total"""
        pass
```

**Factory (`__init__.py`):**

```python
from .ccxt_wallet import CCXTWallet
from .bybit_wallet import BybitWallet

def get_wallet(exchange: str):
    """Factory pour choisir le bon wallet"""
    wallets = {
        'binance': CCXTWallet,
        'bybit': BybitWallet,  # SDK dédié pour UTA
        'okx': CCXTWallet,
        'kucoin': CCXTWallet,
    }
    return wallets.get(exchange, CCXTWallet)(exchange)
```

---

## 🔐 Variables d'environnement

**Fichier `.env` sur VPS:**

```bash
# Binance
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret

# Bybit
BYBIT_API_KEY=your_key
BYBIT_SECRET=your_secret

# OKX
OKX_API_KEY=your_key
OKX_SECRET=your_secret
OKX_PASSPHRASE=your_passphrase

# KuCoin
KUCOIN_API_KEY=your_key
KUCOIN_SECRET=your_secret
KUCOIN_PASSPHRASE=your_passphrase

# Exchange actif
ACTIVE_EXCHANGE=bybit
```

---

## ✅ Plan d'action

1. **Phase 1:** Installer CCXT et tester avec Bybit
2. **Phase 2:** Si CCXT insuffisant pour Bybit UTA, ajouter `pybit`
3. **Phase 3:** Encapsuler dans interface commune `BaseWallet`
4. **Phase 4:** Ajouter autres exchanges (Binance, OKX, KuCoin)

**Temps estimé:** 2-3 heures pour Phase 1+2

---

## 📝 Checklist

- [ ] `pip install ccxt pybit python-binance python-kucoin okx`
- [ ] Créer `api/exchanges/ccxt_wallet.py`
- [ ] Tester `/api/wallet/unified` avec CCXT
- [ ] Si besoin, créer `api/exchanges/bybit_wallet.py` avec pybit
- [ ] Ajouter variables d'environnement `.env`
- [ ] Documenter dans VERIFY_REPORT.md

---

## 🆘 Support communautés

- **CCXT:** https://github.com/ccxt/ccxt/issues
- **Bybit:** https://github.com/bybit-exchange/pybit/issues
- **Binance:** https://dev.binance.vision/
- **OKX:** https://www.okx.com/support/hc/en-us/categories/360000090812-API
- **KuCoin:** https://www.kucoin.com/support/360015102374
