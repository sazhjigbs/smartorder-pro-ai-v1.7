# 📚 SmartOrder PRO - API Documentation

## Vue d'ensemble

Documentation complète de toutes les APIs et modules du bot SmartOrder PRO.

---

## 🔌 Exchange Connectors

### BybitConnector

```python
from exchange_connectors.bybit_connector import BybitConnector

# Initialisation
bybit = BybitConnector(api_key="YOUR_KEY", api_secret="YOUR_SECRET", testnet=False)

# Méthodes principales
balance = bybit.get_balance()
price = bybit.get_current_price("BTCUSDT")
order = bybit.place_order(symbol="BTCUSDT", side="Buy", qty=0.001, price=45000)
positions = bybit.get_positions()
```

#### Méthodes disponibles

| Méthode | Description | Retour |
|---------|-------------|--------|
| `get_balance()` | Récupère le solde du compte | `Dict[str, float]` |
| `get_current_price(symbol)` | Prix actuel d'une paire | `float` |
| `place_order(...)` | Place un ordre | `Dict` |
| `cancel_order(order_id)` | Annule un ordre | `bool` |
| `get_positions()` | Positions ouvertes | `List[Dict]` |
| `get_order_history()` | Historique des ordres | `List[Dict]` |

### BinanceConnector

```python
from exchange_connectors.binance_connector import BinanceConnector

binance = BinanceConnector(api_key="YOUR_KEY", api_secret="YOUR_SECRET")

# Même interface que BybitConnector
balance = binance.get_balance()
```

### OKXConnector / KuCoinConnector

Interface identique aux connecteurs Bybit et Binance.

---

## 🔀 Exchange Router

```python
from core.exchange_router import ExchangeRouter

router = ExchangeRouter()

# Sélection automatique du meilleur exchange
best_exchange = router.select_best_exchange(
    symbol="BTCUSDT",
    order_size=1000  # USD
)

# Récupérer les métriques de tous les exchanges
metrics = router.get_all_exchange_metrics()
```

### Configuration

```json
{
  "selection_criteria": {
    "fees_weight": 0.3,
    "liquidity_weight": 0.4,
    "latency_weight": 0.3
  },
  "fallback_exchanges": ["binance", "okx", "kucoin"]
}
```

---

## 🛡️ Security Manager

```python
from security.database_encryption import SecurityManager

# Chiffrement de clés API
security = SecurityManager()
encrypted = security.encrypt_api_key("YOUR_API_KEY")
decrypted = security.decrypt_api_key(encrypted)

# Rotation de la master key
security.rotate_master_key(new_key="NEW_32_BYTE_KEY")
```

---

## 🔴 Circuit Breaker

```python
from monitoring.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)

@breaker.call
def risky_operation():
    # Votre code ici
    pass

# Vérifier l'état
if breaker.state == "OPEN":
    print("Circuit ouvert, opération bloquée")
```

### États possibles

- **CLOSED**: Normal, opérations autorisées
- **OPEN**: Circuit ouvert, toutes opérations bloquées
- **HALF_OPEN**: Test de récupération

---

## 🔄 Failover Manager

```python
from core.failover_manager import FailoverManager

failover = FailoverManager(primary_exchange="bybit")

# Vérification automatique et switch si nécessaire
current = failover.get_current_exchange()

# Forcer un switch
failover.switch_to_backup_exchange()
```

---

## 📊 Performance Tracker

```python
from utils.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()

# Enregistrer un trade
tracker.add_trade({
    "symbol": "BTCUSDT",
    "side": "BUY",
    "size": 0.01,
    "entry_price": 45000,
    "exit_price": 46000,
    "pnl": 10.0
})

# Obtenir les métriques
metrics = tracker.get_metrics()
print(f"Win Rate: {metrics['win_rate']}%")
print(f"Profit Factor: {metrics['profit_factor']}")

# Sauvegarder les données
tracker.save("data/performance.json")
```

### Métriques calculées

- **total_trades**: Nombre total de trades
- **wins / losses**: Nombre de gains/pertes
- **win_rate**: Taux de réussite (%)
- **total_pnl**: PnL total
- **avg_win / avg_loss**: Moyenne des gains/pertes
- **profit_factor**: Ratio profit/perte
- **best_trade / worst_trade**: Meilleur/pire trade

---

## 🌐 WebSocket Server

```python
from web.websocket_server import WebSocketServer
import asyncio

server = WebSocketServer(host='localhost', port=8765)

# Démarrer le serveur
asyncio.run(server.start())

# Broadcaster des données (depuis un autre thread)
await server.broadcast({
    "type": "price_update",
    "symbol": "BTCUSDT",
    "price": 45000
})
```

### Messages supportés

```json
{
  "type": "price_update",
  "symbol": "BTCUSDT",
  "price": 45000,
  "timestamp": "2024-10-27T10:00:00Z"
}
```

```json
{
  "type": "position_update",
  "symbol": "BTCUSDT",
  "side": "LONG",
  "size": 0.5,
  "pnl": 125.50
}
```

---

## 🤖 Telegram Bot

```python
from telegram.advanced_bot import AdvancedTelegramBot

bot = AdvancedTelegramBot(token="YOUR_BOT_TOKEN")
bot.run()
```

### Commandes disponibles

| Commande | Description |
|----------|-------------|
| `/start` | Menu principal avec boutons interactifs |
| `/status` | Statut du bot et de l'exchange actif |
| `/balance` | Solde du compte et PnL |
| `/positions` | Positions ouvertes |
| `/analytics` | Métriques de performance |
| `/report` | Rapport journalier complet |
| `/pause` | Mettre le trading en pause |
| `/resume` | Reprendre le trading |

---

## 🌐 Web Config Manager

### Routes API

#### GET `/api/config`
Récupère la configuration actuelle.

**Réponse:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "strategy": "scalping",
  "risk_per_trade": 2,
  "max_positions": 3,
  "stop_loss": 1.5,
  "take_profit": 3.0
}
```

#### POST `/api/config`
Sauvegarde une nouvelle configuration.

**Requête:**
```json
{
  "symbol": "ETHUSDT",
  "timeframe": "15m",
  "strategy": "swing",
  "risk_per_trade": 3,
  "max_positions": 5,
  "stop_loss": 2.0,
  "take_profit": 4.0
}
```

**Réponse:**
```json
{
  "status": "success",
  "message": "Config saved successfully"
}
```

---

## 📝 Logging

```python
from utils.centralized_logger import get_logger

logger = get_logger("module_name")

logger.info("Message d'information")
logger.warning("Avertissement")
logger.error("Erreur", exc_info=True)
logger.critical("Erreur critique")
```

### Format des logs

```json
{
  "timestamp": "2024-10-27T10:00:00Z",
  "level": "INFO",
  "module": "bybit_connector",
  "message": "Order placed successfully",
  "data": {
    "order_id": "12345",
    "symbol": "BTCUSDT",
    "side": "BUY"
  }
}
```

---

## 🔧 Health Monitor

```python
from monitoring.exchange_health_monitor import ExchangeHealthMonitor

monitor = ExchangeHealthMonitor()

# Vérifier la santé d'un exchange
health = monitor.check_exchange_health("bybit")

if health['status'] == 'healthy':
    print(f"Latency: {health['latency_ms']}ms")
    print(f"Error rate: {health['error_rate']}%")
```

---

## 📈 Risk Manager

```python
from strategies.risk_manager import RiskManager

risk = RiskManager(
    max_position_size=1000,  # USD
    max_daily_loss=500,      # USD
    max_open_positions=3
)

# Vérifier si on peut ouvrir une position
can_trade = risk.can_open_position(size=200)

# Calculer la taille de position recommandée
size = risk.calculate_position_size(
    account_balance=10000,
    risk_percent=2,
    stop_loss_distance=1.5  # %
)
```

---

## 🧪 Testing

```python
# Test d'un connecteur
pytest tests/test_bybit_connector.py -v

# Test du router
pytest tests/test_exchange_router.py -v

# Test E2E
pytest tests/test_e2e.py -v

# Pre-production check
python tests/pre_prod_check.py
```

---

## 🔐 Variables d'environnement

```env
# Exchange APIs
BYBIT_API_KEY=
BYBIT_API_SECRET=
BINANCE_API_KEY=
BINANCE_API_SECRET=
OKX_API_KEY=
OKX_API_SECRET=
OKX_PASSPHRASE=
KUCOIN_API_KEY=
KUCOIN_API_SECRET=
KUCOIN_PASSPHRASE=

# Telegram
TELEGRAM_BOT_TOKEN=

# Security
MASTER_KEY=

# Logging
LOG_LEVEL=INFO
```

---

## 🚨 Error Handling

Tous les modules utilisent des exceptions personnalisées :

```python
from core.exceptions import (
    ExchangeConnectionError,
    InsufficientBalanceError,
    OrderPlacementError,
    CircuitBreakerOpenError
)

try:
    order = bybit.place_order(...)
except OrderPlacementError as e:
    logger.error(f"Failed to place order: {e}")
except InsufficientBalanceError:
    logger.warning("Insufficient balance")
```

---

## 📞 Support

- GitHub Issues: [Lien vers repo]
- Email: support@smartorderpro.com
- Documentation complète: README.md

---

**Dernière mise à jour: 2024 - v1.9-FINAL**
