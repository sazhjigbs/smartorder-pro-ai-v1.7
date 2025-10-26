# 🚨 PRÉREQUIS CRITIQUES AVANT DE CONTINUER

**Date :** 26 Octobre 2025, 00:05 UTC  
**Objectif :** Éviter les problèmes futurs en ajoutant ces éléments maintenant

---

## ⚠️ CE QUI MANQUE ET QUI EST CRITIQUE

### 🔴 1. SYSTÈME DE BACKUP AUTOMATIQUE (TRÈS IMPORTANT)

**Problème :** Si tu casses quelque chose pendant le dev, tu peux tout perdre.

**Solution à ajouter MAINTENANT :**

```python
# tools/auto_backup.py

import shutil
import os
from datetime import datetime
import schedule
import time

class AutoBackup:
    def __init__(self):
        self.backup_dir = "C:/Backups/smartorder/"
        self.source_dir = "C:/Users/aimet/smartorder-pro-ai-v1.7/"
        
        # Crée dossier backup
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self):
        """Crée backup horodaté"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"smartorder_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Exclut node_modules, __pycache__, .git
        def ignore_patterns(dir, files):
            return [f for f in files if f in ['node_modules', '__pycache__', '.git', 'venv']]
        
        shutil.copytree(
            self.source_dir, 
            backup_path,
            ignore=ignore_patterns
        )
        
        print(f"✅ Backup créé : {backup_path}")
        
        # Garde seulement les 7 derniers backups
        self.cleanup_old_backups()
    
    def cleanup_old_backups(self):
        """Supprime backups > 7 jours"""
        backups = sorted(os.listdir(self.backup_dir))
        
        if len(backups) > 7:
            for old_backup in backups[:-7]:
                old_path = os.path.join(self.backup_dir, old_backup)
                shutil.rmtree(old_path)
                print(f"🗑️ Supprimé ancien backup : {old_backup}")
    
    def start_scheduled_backup(self):
        """Backup automatique toutes les 6 heures"""
        schedule.every(6).hours.do(self.create_backup)
        
        print("🔄 Auto-backup activé (toutes les 6h)")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check chaque minute

# Lancer
if __name__ == "__main__":
    backup = AutoBackup()
    backup.create_backup()  # Backup immédiat
    backup.start_scheduled_backup()
```

**Pourquoi c'est critique :**
- Évite de perdre des heures de travail
- Permet de revenir en arrière facilement
- Sauvegarde automatique toutes les 6h

**Installation :**
```bash
pip install schedule
python tools/auto_backup.py &  # Lance en background
```

---

### 🔴 2. SYSTÈME DE TESTS UNITAIRES (TRÈS IMPORTANT)

**Problème :** Aucun test = tu ne sais pas si tu casses quelque chose.

**Solution à ajouter MAINTENANT :**

```python
# tests/test_core.py

import pytest
from core.bybit_client import BybitClient
from core.hybrid_capital_manager import HybridCapitalManager
from core.router import choose_exchange

class TestBybitClient:
    def test_connection(self):
        """Test connexion Bybit"""
        client = BybitClient()
        assert client is not None
    
    def test_fetch_balance(self):
        """Test récupération balance"""
        client = BybitClient()
        balance = client.get_balance()
        assert balance >= 0

class TestCapitalManager:
    def test_allocation(self):
        """Test allocation capital"""
        manager = HybridCapitalManager(total_capital=1000)
        allocation = manager.allocate_for_position(risk_pct=2)
        
        assert allocation == 20  # 2% de 1000
        assert allocation <= 1000

class TestRouter:
    def test_exchange_selection(self):
        """Test sélection exchange"""
        exchange = choose_exchange("BTCUSDT", 0.001, 67000)
        
        assert exchange in ["bybit", "binance", "kucoin"]

# Lancer tests
# pytest tests/ -v
```

**Pourquoi c'est critique :**
- Détecte les régressions immédiatement
- Permet de coder avec confiance
- Documente le comportement attendu

**Installation :**
```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

### 🟠 3. LOGGING STRUCTURÉ (IMPORTANT)

**Problème :** Actuellement les logs sont basiques, difficile de debugger.

**Solution à ajouter MAINTENANT :**

```python
# core/logger.py

import logging
import json
from datetime import datetime
from pathlib import Path

class StructuredLogger:
    def __init__(self, name="smartorder"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Crée dossier logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Handler fichier JSON
        json_handler = logging.FileHandler(
            f"logs/{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        json_handler.setFormatter(JSONFormatter())
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        self.logger.addHandler(json_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message, **kwargs):
        self.logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": message,
            **kwargs
        }))
    
    def error(self, message, **kwargs):
        self.logger.error(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": message,
            **kwargs
        }))
    
    def trade(self, action, symbol, price, quantity, **kwargs):
        """Log spécial pour trades"""
        self.info("TRADE", 
            action=action,
            symbol=symbol, 
            price=price,
            quantity=quantity,
            **kwargs
        )

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

# Usage
logger = StructuredLogger()
logger.info("Bot démarré")
logger.trade("BUY", "BTCUSDT", 67000, 0.001, exchange="bybit")
```

**Pourquoi c'est critique :**
- Logs structurés faciles à parser
- Historique complet des trades
- Debug facile avec logs JSON

---

### 🟠 4. CONFIGURATION CENTRALISÉE (IMPORTANT)

**Problème :** Config éparpillée dans le code, difficile à maintenir.

**Solution à ajouter MAINTENANT :**

```python
# config/settings.py

from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Exchanges
    EXCHANGES_ENABLED: List[str] = ["bybit"]
    PRIMARY_EXCHANGE: str = "bybit"
    
    # Bybit
    BYBIT_API_KEY: str
    BYBIT_API_SECRET: str
    BYBIT_TESTNET: bool = False
    
    # Binance
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    
    # KuCoin
    KUCOIN_API_KEY: str = ""
    KUCOIN_API_SECRET: str = ""
    KUCOIN_API_PASSPHRASE: str = ""
    
    # Trading
    MAX_EXPOSURE_PCT: float = 80.0
    SAFETY_BUFFER_PCT: float = 5.0
    MAX_POSITIONS_TOTAL: int = 20
    DEFAULT_LEVERAGE: int = 2
    
    # Risk
    MAX_RISK_PER_TRADE_PCT: float = 2.0
    MAX_DRAWDOWN_PCT: float = 10.0
    STOP_LOSS_PCT: float = 2.0
    
    # Fees
    PREFER_MAKER_ORDERS: bool = True
    MAX_SLIPPAGE_PCT: float = 0.3
    
    # Rate Limits
    ENABLE_RATE_LIMIT_QUEUE: bool = True
    BATCH_ORDERS_ENABLED: bool = True
    BATCH_INTERVAL_MS: int = 500
    
    # Monitoring
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    ENABLE_NOTIFICATIONS: bool = True
    
    # Backup
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 6
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton
settings = Settings()

# Usage
from config.settings import settings

if settings.BYBIT_TESTNET:
    print("Mode TESTNET activé")
```

**config/.env.example** (à créer) :
```bash
# Exchanges
EXCHANGES_ENABLED=bybit,binance,kucoin
PRIMARY_EXCHANGE=bybit

# Bybit
BYBIT_API_KEY=your_key_here
BYBIT_API_SECRET=your_secret_here
BYBIT_TESTNET=false

# Trading
MAX_EXPOSURE_PCT=80.0
DEFAULT_LEVERAGE=2

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

**Pourquoi c'est critique :**
- Configuration centralisée
- Validation automatique (Pydantic)
- Facile à modifier sans toucher le code
- Type-safe

**Installation :**
```bash
pip install pydantic python-dotenv
```

---

### 🟡 5. MONITORING SANTÉ EN TEMPS RÉEL (UTILE)

**Problème :** Tu ne sais pas si le bot tourne bien en continu.

**Solution à ajouter MAINTENANT :**

```python
# core/health_checker.py

import psutil
import time
from datetime import datetime
from core.logger import StructuredLogger

logger = StructuredLogger()

class HealthChecker:
    def __init__(self):
        self.start_time = datetime.now()
        self.last_trade_time = None
        self.trade_count = 0
        self.error_count = 0
    
    def check_system(self):
        """Vérifie santé système"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        health = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "cpu_percent": cpu,
            "memory_percent": memory,
            "disk_percent": disk,
            "trade_count": self.trade_count,
            "error_count": self.error_count,
            "status": "healthy" if cpu < 80 and memory < 80 else "warning"
        }
        
        logger.info("HEALTH_CHECK", **health)
        
        return health
    
    def increment_trade(self):
        self.trade_count += 1
        self.last_trade_time = datetime.now()
    
    def increment_error(self):
        self.error_count += 1
    
    def get_status(self):
        """Status pour API"""
        health = self.check_system()
        
        return {
            **health,
            "last_trade": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "avg_trades_per_hour": self.trade_count / (health["uptime_seconds"] / 3600) if health["uptime_seconds"] > 0 else 0
        }

# Endpoint API
from fastapi import APIRouter

router = APIRouter()
health_checker = HealthChecker()

@router.get("/health")
def health():
    return health_checker.get_status()
```

**Pourquoi c'est utile :**
- Surveillance continue
- Détecte problèmes rapidement
- Métriques de performance

---

### 🟡 6. MODE SIMULATION OBLIGATOIRE (UTILE)

**Problème :** Tester en LIVE = risque de perdre de l'argent.

**Solution à ajouter MAINTENANT :**

```python
# core/simulation_mode.py

from config.settings import settings

class SimulationManager:
    def __init__(self):
        self.simulation_mode = settings.SIMULATION_MODE
        self.virtual_balance = 10000.0  # USDT virtuels
        self.virtual_positions = {}
    
    def place_order(self, symbol, side, quantity, price):
        """Place ordre (réel ou simulé)"""
        
        if self.simulation_mode:
            # Mode simulation
            print(f"🎮 [SIMULATION] {side} {quantity} {symbol} @ {price}")
            
            # Simule exécution
            self.virtual_positions[symbol] = {
                "side": side,
                "quantity": quantity,
                "entry_price": price,
                "pnl": 0
            }
            
            return {"status": "simulated", "order_id": f"SIM_{symbol}"}
        
        else:
            # Mode réel
            print(f"⚠️ [LIVE] {side} {quantity} {symbol} @ {price}")
            
            # Confirmation obligatoire pour ordres > 100 USDT
            if quantity * price > 100:
                confirm = input("⚠️ Ordre > 100 USDT. Confirmer ? (yes/no): ")
                if confirm.lower() != "yes":
                    return {"status": "cancelled", "reason": "user_cancelled"}
            
            # Place ordre réel
            from core.bybit_client import BybitClient
            client = BybitClient()
            return client.place_order(symbol, side, quantity, price)
    
    def get_balance(self):
        """Balance (réelle ou virtuelle)"""
        if self.simulation_mode:
            return self.virtual_balance
        else:
            from core.bybit_client import BybitClient
            client = BybitClient()
            return client.get_balance()

# Usage
sim = SimulationManager()
sim.place_order("BTCUSDT", "BUY", 0.001, 67000)
```

**config/.env** (ajouter) :
```bash
SIMULATION_MODE=true  # false pour mode LIVE
```

**Pourquoi c'est utile :**
- Test sans risque
- Validation stratégies
- Confirmation obligatoire pour gros ordres

---

## 📋 CHECKLIST AVANT DE COMMENCER

Avant de continuer le développement, assure-toi d'avoir :

### Critique (À faire MAINTENANT) :
- [ ] **Auto-backup** - Sauvegarde toutes les 6h
- [ ] **Tests unitaires** - pytest configuré
- [ ] **Logging structuré** - Logs JSON

### Important (À faire cette semaine) :
- [ ] **Configuration centralisée** - Pydantic Settings
- [ ] **Health checker** - Monitoring système
- [ ] **Mode simulation** - Tests sans risque

### Optionnel (Peut attendre) :
- [ ] Documentation API (Swagger)
- [ ] CI/CD (GitHub Actions)
- [ ] Alertes Discord/Email

---

## 🎯 INSTALLATION RAPIDE DES PRÉREQUIS

```bash
# 1. Installe dépendances
pip install schedule pytest pytest-asyncio pydantic python-dotenv psutil

# 2. Crée structure
mkdir -p tests logs config backups

# 3. Copie fichiers
# (Créer les fichiers Python ci-dessus)

# 4. Lance backup initial
python tools/auto_backup.py

# 5. Lance tests
pytest tests/ -v

# 6. Vérifie health
curl http://localhost:8555/health
```

---

## 💡 AUTRES IDÉES À CONSIDÉRER

### 1. **Database Migration System** (Utile pour Phase 14)
```bash
pip install alembic
alembic init migrations
```

### 2. **Pre-commit Hooks** (Qualité code)
```bash
pip install pre-commit
# .pre-commit-config.yaml avec black, flake8, mypy
```

### 3. **Environment Validator** (Sécurité)
```python
# Vérifie que toutes les variables .env sont présentes au démarrage
def validate_env():
    required = ["BYBIT_API_KEY", "TELEGRAM_BOT_TOKEN"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise Exception(f"Missing env vars: {missing}")
```

### 4. **Kill Switch** (Sécurité ultime)
```python
# Arrêt d'urgence via Telegram
@bot.command("/emergency_stop")
def emergency_stop():
    # Ferme toutes positions
    # Arrête le bot
    # Envoie notification
```

### 5. **Performance Metrics** (Analyse)
```python
# Temps d'exécution des fonctions critiques
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info("PERFORMANCE", 
            function=func.__name__,
            duration_ms=duration * 1000
        )
        
        return result
    return wrapper

@timing_decorator
def place_order(...):
    ...
```

---

## 🚀 ORDRE D'AJOUT RECOMMANDÉ

Si tu dois prioriser, fais dans cet ordre :

1. **Auto-backup** (10 min) - Évite de perdre ton travail
2. **Logging structuré** (15 min) - Debug facile
3. **Configuration centralisée** (20 min) - Code propre
4. **Tests unitaires** (30 min) - Confiance dans le code
5. **Mode simulation** (15 min) - Test sans risque
6. **Health checker** (10 min) - Monitoring

**Temps total : ~1h40** pour sécuriser ton projet avant de continuer !

---

## 🎯 MA RECOMMANDATION FINALE

**AVANT de commencer les phases 6.11-6.14, ajoute AU MINIMUM :**

1. ✅ **Auto-backup** - C'est non-négociable
2. ✅ **Logging structuré** - Tu vas en avoir besoin
3. ✅ **Tests unitaires** - Pour les nouvelles features

Les 3 autres (config, health, simulation) sont très utiles mais pas bloquants.

**Une fois ces 3 éléments en place, tu peux coder sereinement ! 🚀**

---

**Veux-tu que je commence par créer ces fichiers de base ? Ou tu préfères commencer directement avec les phases IA ?**
