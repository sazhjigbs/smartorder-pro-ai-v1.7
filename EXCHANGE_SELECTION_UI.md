# 🎛️ SÉLECTION MULTI-EXCHANGE - Interface Utilisateur

**Date :** 25 Octobre 2025  
**Objectif :** Permettre à l'utilisateur de choisir les exchanges actifs

---

## 💡 CONCEPT

L'utilisateur doit pouvoir :
- ✅ **Activer/Désactiver** chaque exchange (Bybit, Binance, KuCoin)
- ✅ **Voir le statut** de connexion en temps réel
- ✅ **Répartir le capital** entre exchanges
- ✅ **Définir exchange principal** pour priorité
- ✅ **Contrôler via Dashboard Web ou Telegram**

---

## 🎯 MODULE 1 : DATABASE SCHEMA

### Table `exchange_settings`

```sql
CREATE TABLE exchange_settings (
    id SERIAL PRIMARY KEY,
    exchange_name VARCHAR(50) NOT NULL UNIQUE,  -- bybit, binance, kucoin
    is_enabled BOOLEAN DEFAULT false,
    is_primary BOOLEAN DEFAULT false,
    
    -- API Credentials
    api_key TEXT,
    api_secret TEXT,
    api_passphrase TEXT,  -- Pour KuCoin uniquement
    
    -- Capital Allocation
    capital_allocation_pct DECIMAL(5,2) DEFAULT 0.00,  -- % du capital total
    max_positions INT DEFAULT 5,
    
    -- Préférences
    prefer_spot BOOLEAN DEFAULT true,
    prefer_futures BOOLEAN DEFAULT false,
    max_leverage INT DEFAULT 10,
    
    -- Status
    connection_status VARCHAR(20) DEFAULT 'disconnected',
    last_connected TIMESTAMP,
    last_error TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_enabled_exchanges ON exchange_settings(is_enabled);
CREATE INDEX idx_primary_exchange ON exchange_settings(is_primary);

-- Insert defaults
INSERT INTO exchange_settings (exchange_name, is_enabled, is_primary) VALUES
('bybit', true, true),
('binance', false, false),
('kucoin', false, false);
```

---

## 🎯 MODULE 2 : BACKEND API

### Exchange Manager Service

```python
# services/exchange_manager.py

from typing import List, Dict
import ccxt
from database import db

class ExchangeManager:
    def __init__(self):
        self.active_exchanges = {}
        self.load_exchanges()
    
    def load_exchanges(self):
        """Charge exchanges depuis DB"""
        settings = db.query("""
            SELECT * FROM exchange_settings 
            WHERE is_enabled = true
        """)
        
        for setting in settings:
            self.init_exchange(setting)
    
    def init_exchange(self, setting):
        """Initialise connexion exchange"""
        exchange_name = setting['exchange_name']
        
        try:
            if exchange_name == 'bybit':
                exchange = ccxt.bybit({
                    'apiKey': setting['api_key'],
                    'secret': setting['api_secret'],
                    'enableRateLimit': True
                })
            
            elif exchange_name == 'binance':
                exchange = ccxt.binance({
                    'apiKey': setting['api_key'],
                    'secret': setting['api_secret'],
                    'enableRateLimit': True
                })
            
            elif exchange_name == 'kucoin':
                exchange = ccxt.kucoin({
                    'apiKey': setting['api_key'],
                    'secret': setting['api_secret'],
                    'password': setting['api_passphrase'],
                    'enableRateLimit': True
                })
            
            # Test connexion
            balance = exchange.fetch_balance()
            
            # Update status
            db.execute("""
                UPDATE exchange_settings 
                SET connection_status = 'connected',
                    last_connected = NOW(),
                    last_error = NULL
                WHERE exchange_name = %s
            """, [exchange_name])
            
            self.active_exchanges[exchange_name] = {
                'client': exchange,
                'settings': setting
            }
            
            print(f"✅ {exchange_name} connected")
            
        except Exception as e:
            print(f"❌ {exchange_name} failed: {e}")
            
            db.execute("""
                UPDATE exchange_settings 
                SET connection_status = 'error',
                    last_error = %s
                WHERE exchange_name = %s
            """, [str(e), exchange_name])
    
    def get_active_exchanges(self) -> List[str]:
        """Liste exchanges actifs"""
        return list(self.active_exchanges.keys())
    
    def get_primary_exchange(self) -> str:
        """Récupère exchange principal"""
        result = db.query("""
            SELECT exchange_name FROM exchange_settings 
            WHERE is_primary = true AND is_enabled = true
            LIMIT 1
        """)
        
        return result[0]['exchange_name'] if result else None
    
    def toggle_exchange(self, exchange_name: str, enable: bool):
        """Active/Désactive exchange"""
        db.execute("""
            UPDATE exchange_settings 
            SET is_enabled = %s, updated_at = NOW()
            WHERE exchange_name = %s
        """, [enable, exchange_name])
        
        if enable:
            # Charge exchange
            setting = db.query("""
                SELECT * FROM exchange_settings 
                WHERE exchange_name = %s
            """, [exchange_name])[0]
            
            self.init_exchange(setting)
        else:
            # Décharge exchange
            if exchange_name in self.active_exchanges:
                del self.active_exchanges[exchange_name]
    
    def set_primary_exchange(self, exchange_name: str):
        """Définit exchange principal"""
        # Reset tous
        db.execute("UPDATE exchange_settings SET is_primary = false")
        
        # Set nouveau primary
        db.execute("""
            UPDATE exchange_settings 
            SET is_primary = true 
            WHERE exchange_name = %s
        """, [exchange_name])
    
    def update_capital_allocation(self, allocations: Dict[str, float]):
        """
        Met à jour répartition capital
        allocations = {'bybit': 50.0, 'binance': 30.0, 'kucoin': 20.0}
        """
        total = sum(allocations.values())
        
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Total doit être 100%, actuellement {total}%")
        
        for exchange_name, pct in allocations.items():
            db.execute("""
                UPDATE exchange_settings 
                SET capital_allocation_pct = %s
                WHERE exchange_name = %s
            """, [pct, exchange_name])
    
    def get_exchange_status(self) -> List[Dict]:
        """Récupère statut de tous les exchanges"""
        return db.query("""
            SELECT 
                exchange_name,
                is_enabled,
                is_primary,
                capital_allocation_pct,
                connection_status,
                last_connected,
                last_error
            FROM exchange_settings
            ORDER BY is_primary DESC, exchange_name
        """)

# Singleton global
exchange_manager = ExchangeManager()
```

---

## 🎯 MODULE 3 : API ENDPOINTS (FastAPI)

```python
# api/routes/exchanges.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services.exchange_manager import exchange_manager

router = APIRouter(prefix="/api/exchanges", tags=["Exchanges"])

class ToggleExchangeRequest(BaseModel):
    exchange_name: str
    enable: bool

class SetPrimaryRequest(BaseModel):
    exchange_name: str

class CapitalAllocationRequest(BaseModel):
    allocations: Dict[str, float]  # {'bybit': 50, 'binance': 30, 'kucoin': 20}

class UpdateAPIKeysRequest(BaseModel):
    exchange_name: str
    api_key: str
    api_secret: str
    api_passphrase: str = None

@router.get("/status")
async def get_exchanges_status():
    """Récupère statut de tous les exchanges"""
    try:
        status = exchange_manager.get_exchange_status()
        return {"success": True, "exchanges": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle")
async def toggle_exchange(request: ToggleExchangeRequest):
    """Active/Désactive un exchange"""
    try:
        exchange_manager.toggle_exchange(
            request.exchange_name, 
            request.enable
        )
        
        return {
            "success": True, 
            "message": f"{request.exchange_name} {'enabled' if request.enable else 'disabled'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-primary")
async def set_primary_exchange(request: SetPrimaryRequest):
    """Définit exchange principal"""
    try:
        exchange_manager.set_primary_exchange(request.exchange_name)
        return {"success": True, "primary": request.exchange_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/capital-allocation")
async def update_capital_allocation(request: CapitalAllocationRequest):
    """Met à jour répartition capital"""
    try:
        exchange_manager.update_capital_allocation(request.allocations)
        return {"success": True, "allocations": request.allocations}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-keys")
async def update_api_keys(request: UpdateAPIKeysRequest):
    """Met à jour clés API"""
    try:
        from database import db
        
        db.execute("""
            UPDATE exchange_settings 
            SET api_key = %s,
                api_secret = %s,
                api_passphrase = %s,
                updated_at = NOW()
            WHERE exchange_name = %s
        """, [
            request.api_key,
            request.api_secret,
            request.api_passphrase,
            request.exchange_name
        ])
        
        # Reconnecte
        exchange_manager.toggle_exchange(request.exchange_name, True)
        
        return {"success": True, "message": "API keys updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_exchanges():
    """Liste exchanges actifs"""
    try:
        active = exchange_manager.get_active_exchanges()
        primary = exchange_manager.get_primary_exchange()
        
        return {
            "success": True,
            "active_exchanges": active,
            "primary_exchange": primary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎯 MODULE 4 : DASHBOARD WEB (React)

### Component ExchangeSelector

```jsx
// components/ExchangeSelector.jsx

import React, { useState, useEffect } from 'react';
import { Switch, Slider, Badge, Button, Alert } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, StarOutlined } from '@ant-design/icons';

const ExchangeSelector = () => {
    const [exchanges, setExchanges] = useState([]);
    const [allocations, setAllocations] = useState({});
    
    useEffect(() => {
        fetchExchanges();
    }, []);
    
    const fetchExchanges = async () => {
        const response = await fetch('/api/exchanges/status');
        const data = await response.json();
        
        setExchanges(data.exchanges);
        
        // Init allocations
        const allocs = {};
        data.exchanges.forEach(ex => {
            allocs[ex.exchange_name] = ex.capital_allocation_pct;
        });
        setAllocations(allocs);
    };
    
    const toggleExchange = async (exchangeName, enable) => {
        await fetch('/api/exchanges/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exchange_name: exchangeName, enable })
        });
        
        fetchExchanges();
    };
    
    const setPrimary = async (exchangeName) => {
        await fetch('/api/exchanges/set-primary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exchange_name: exchangeName })
        });
        
        fetchExchanges();
    };
    
    const updateAllocations = async () => {
        const total = Object.values(allocations).reduce((a, b) => a + b, 0);
        
        if (Math.abs(total - 100) > 0.01) {
            alert('Total doit être 100%');
            return;
        }
        
        await fetch('/api/exchanges/capital-allocation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ allocations })
        });
        
        alert('✅ Capital allocation updated');
    };
    
    const getStatusBadge = (status) => {
        if (status === 'connected') {
            return <Badge status="success" text="Connected" />;
        } else if (status === 'error') {
            return <Badge status="error" text="Error" />;
        } else {
            return <Badge status="default" text="Disconnected" />;
        }
    };
    
    return (
        <div className="exchange-selector">
            <h2>🌐 Multi-Exchange Configuration</h2>
            
            {exchanges.map(ex => (
                <div key={ex.exchange_name} className="exchange-card">
                    <div className="exchange-header">
                        <div className="exchange-info">
                            <h3>
                                {ex.exchange_name.toUpperCase()}
                                {ex.is_primary && (
                                    <StarOutlined style={{ color: 'gold', marginLeft: 10 }} />
                                )}
                            </h3>
                            {getStatusBadge(ex.connection_status)}
                        </div>
                        
                        <Switch 
                            checked={ex.is_enabled}
                            onChange={(checked) => toggleExchange(ex.exchange_name, checked)}
                        />
                    </div>
                    
                    {ex.is_enabled && (
                        <>
                            <div className="exchange-details">
                                <div>
                                    <label>Capital Allocation:</label>
                                    <Slider 
                                        min={0} 
                                        max={100}
                                        value={allocations[ex.exchange_name] || 0}
                                        onChange={(val) => setAllocations({
                                            ...allocations,
                                            [ex.exchange_name]: val
                                        })}
                                        marks={{
                                            0: '0%',
                                            50: '50%',
                                            100: '100%'
                                        }}
                                    />
                                    <span>{allocations[ex.exchange_name] || 0}%</span>
                                </div>
                                
                                {!ex.is_primary && (
                                    <Button 
                                        size="small"
                                        onClick={() => setPrimary(ex.exchange_name)}
                                    >
                                        Set as Primary
                                    </Button>
                                )}
                            </div>
                            
                            {ex.last_error && (
                                <Alert 
                                    type="error" 
                                    message={ex.last_error} 
                                    closable 
                                />
                            )}
                        </>
                    )}
                </div>
            ))}
            
            <Button 
                type="primary" 
                onClick={updateAllocations}
                style={{ marginTop: 20 }}
            >
                💾 Save Capital Allocation
            </Button>
            
            <div className="allocation-summary">
                <h4>Total Allocation: {Object.values(allocations).reduce((a, b) => a + b, 0)}%</h4>
            </div>
        </div>
    );
};

export default ExchangeSelector;
```

### CSS Styling

```css
/* styles/ExchangeSelector.css */

.exchange-selector {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
}

.exchange-card {
    background: #1e1e2e;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 15px;
    transition: all 0.3s;
}

.exchange-card:hover {
    border-color: #4a90e2;
    box-shadow: 0 4px 15px rgba(74, 144, 226, 0.2);
}

.exchange-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.exchange-info h3 {
    margin: 0;
    color: #fff;
    font-size: 18px;
}

.exchange-details {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #333;
}

.exchange-details label {
    display: block;
    margin-bottom: 8px;
    color: #aaa;
}

.allocation-summary {
    margin-top: 20px;
    padding: 15px;
    background: #252535;
    border-radius: 8px;
    text-align: center;
}

.allocation-summary h4 {
    margin: 0;
    color: #4a90e2;
}
```

---

## 🎯 MODULE 5 : BOT TELEGRAM

### Commandes Telegram

```python
# telegram/handlers/exchange_handler.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from services.exchange_manager import exchange_manager

async def exchanges_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /exchanges - Affiche menu exchanges"""
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="exchange_status"),
            InlineKeyboardButton("⚙️ Configure", callback_data="exchange_config")
        ],
        [
            InlineKeyboardButton("🔄 Toggle Bybit", callback_data="toggle_bybit"),
        ],
        [
            InlineKeyboardButton("🔄 Toggle Binance", callback_data="toggle_binance"),
        ],
        [
            InlineKeyboardButton("🔄 Toggle KuCoin", callback_data="toggle_kucoin")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 *Multi-Exchange Control*\n\n"
        "Gérez vos exchanges actifs:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def exchange_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche status exchanges"""
    query = update.callback_query
    await query.answer()
    
    exchanges = exchange_manager.get_exchange_status()
    
    message = "📊 *Exchange Status*\n\n"
    
    for ex in exchanges:
        status_emoji = "✅" if ex['connection_status'] == 'connected' else "❌"
        primary_emoji = "⭐" if ex['is_primary'] else ""
        enabled_text = "ON" if ex['is_enabled'] else "OFF"
        
        message += f"{status_emoji} *{ex['exchange_name'].upper()}* {primary_emoji}\n"
        message += f"   • Status: {enabled_text}\n"
        message += f"   • Capital: {ex['capital_allocation_pct']}%\n"
        
        if ex['last_error']:
            message += f"   • Error: {ex['last_error'][:50]}...\n"
        
        message += "\n"
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown'
    )

async def toggle_exchange_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle exchange on/off"""
    query = update.callback_query
    await query.answer()
    
    exchange_name = query.data.replace('toggle_', '')
    
    # Get current status
    exchanges = exchange_manager.get_exchange_status()
    current = next(ex for ex in exchanges if ex['exchange_name'] == exchange_name)
    
    new_status = not current['is_enabled']
    
    # Toggle
    exchange_manager.toggle_exchange(exchange_name, new_status)
    
    status_text = "activé ✅" if new_status else "désactivé ❌"
    
    await query.edit_message_text(
        f"*{exchange_name.upper()}* {status_text}",
        parse_mode='Markdown'
    )

# Register handlers
from telegram.ext import CommandHandler, CallbackQueryHandler

def register_exchange_handlers(application):
    application.add_handler(CommandHandler("exchanges", exchanges_command))
    application.add_handler(CallbackQueryHandler(exchange_status_callback, pattern="^exchange_status$"))
    application.add_handler(CallbackQueryHandler(toggle_exchange_callback, pattern="^toggle_"))
```

---

## 🎯 MODULE 6 : SYSTÈME DE NOTIFICATIONS

### Notifications en temps réel

```python
# services/exchange_notifier.py

import asyncio
from datetime import datetime

class ExchangeNotifier:
    def __init__(self):
        self.subscribers = []  # WebSocket clients
        
    def subscribe(self, client):
        """Subscribe to notifications"""
        self.subscribers.append(client)
    
    def unsubscribe(self, client):
        """Unsubscribe"""
        if client in self.subscribers:
            self.subscribers.remove(client)
    
    async def notify_exchange_status(self, exchange_name, status, error=None):
        """Notifie changement status"""
        
        message = {
            "type": "exchange_status",
            "exchange": exchange_name,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        # Envoie à tous les clients WebSocket
        for client in self.subscribers:
            try:
                await client.send_json(message)
            except:
                self.unsubscribe(client)
        
        # Envoie notification Telegram
        from telegram.bot_instance import bot
        await bot.send_notification(
            f"🔔 {exchange_name.upper()}: {status}"
        )

notifier = ExchangeNotifier()
```

---

## 🎯 MODULE 7 : HEALTH CHECK & AUTO-RECONNECT

### Monitoring continu

```python
# services/exchange_health_monitor.py

import asyncio
from datetime import datetime, timedelta
from services.exchange_manager import exchange_manager
from services.exchange_notifier import notifier

class ExchangeHealthMonitor:
    def __init__(self):
        self.check_interval = 30  # 30 secondes
        self.running = False
    
    async def start(self):
        """Démarre monitoring"""
        self.running = True
        
        while self.running:
            await self.check_all_exchanges()
            await asyncio.sleep(self.check_interval)
    
    async def check_all_exchanges(self):
        """Vérifie santé de tous les exchanges"""
        
        for exchange_name, exchange_data in exchange_manager.active_exchanges.items():
            try:
                # Test connexion
                client = exchange_data['client']
                await client.fetch_balance()
                
                # Update last check
                from database import db
                db.execute("""
                    UPDATE exchange_settings 
                    SET connection_status = 'connected',
                        last_connected = NOW()
                    WHERE exchange_name = %s
                """, [exchange_name])
                
            except Exception as e:
                print(f"❌ {exchange_name} health check failed: {e}")
                
                # Update error status
                from database import db
                db.execute("""
                    UPDATE exchange_settings 
                    SET connection_status = 'error',
                        last_error = %s
                    WHERE exchange_name = %s
                """, [str(e), exchange_name])
                
                # Notify
                await notifier.notify_exchange_status(
                    exchange_name, 
                    'error', 
                    str(e)
                )
                
                # Tente reconnexion
                await self.try_reconnect(exchange_name)
    
    async def try_reconnect(self, exchange_name):
        """Tente reconnexion"""
        print(f"🔄 Attempting to reconnect {exchange_name}...")
        
        try:
            from database import db
            setting = db.query("""
                SELECT * FROM exchange_settings 
                WHERE exchange_name = %s
            """, [exchange_name])[0]
            
            exchange_manager.init_exchange(setting)
            
            await notifier.notify_exchange_status(
                exchange_name, 
                'reconnected'
            )
            
        except Exception as e:
            print(f"❌ Reconnection failed: {e}")
    
    def stop(self):
        """Arrête monitoring"""
        self.running = False

# Singleton
health_monitor = ExchangeHealthMonitor()

# Start on app startup
async def start_health_monitoring():
    asyncio.create_task(health_monitor.start())
```

---

## 📱 EXEMPLES D'UTILISATION

### 1. Dashboard Web
```
Utilisateur visite: http://localhost:3000/settings/exchanges
→ Voit liste exchanges avec switches
→ Active Binance + Bybit
→ Définit Bybit comme primary (⭐)
→ Alloue 60% Bybit, 40% Binance
→ Sauvegarde
```

### 2. Telegram
```
User: /exchanges
Bot: [Menu avec boutons]

User: Clique "Toggle Binance"
Bot: "Binance activé ✅"

User: /exchanges -> Status
Bot: 
📊 Exchange Status

✅ BYBIT ⭐
   • Status: ON
   • Capital: 60%

✅ BINANCE
   • Status: ON
   • Capital: 40%

❌ KUCOIN
   • Status: OFF
   • Capital: 0%
```

### 3. API Direct
```bash
# Activer Binance
curl -X POST http://localhost:8000/api/exchanges/toggle \
  -H "Content-Type: application/json" \
  -d '{"exchange_name": "binance", "enable": true}'

# Définir répartition capital
curl -X POST http://localhost:8000/api/exchanges/capital-allocation \
  -H "Content-Type: application/json" \
  -d '{"allocations": {"bybit": 60, "binance": 40, "kucoin": 0}}'
```

---

## 🔐 SÉCURITÉ

### Chiffrement des API Keys

```python
from cryptography.fernet import Fernet
import os

class APIKeyEncryptor:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY').encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, api_key: str) -> str:
        """Chiffre API key"""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """Déchiffre API key"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()

# Usage dans exchange_manager
encryptor = APIKeyEncryptor()

# Avant stockage DB
encrypted_key = encryptor.encrypt(api_key)

# Avant utilisation
api_key = encryptor.decrypt(encrypted_key)
```

---

## 🎯 ROADMAP DÉVELOPPEMENT

### Phase 1 (3 jours)
- [ ] Database schema + migrations
- [ ] Exchange Manager Service
- [ ] API Endpoints

### Phase 2 (3 jours)
- [ ] Dashboard Web Component
- [ ] Telegram Commands
- [ ] WebSocket notifications

### Phase 3 (2 jours)
- [ ] Health Monitor
- [ ] Auto-reconnect
- [ ] API Key Encryption

**Temps total : 8 jours (~64h)**

---

**Document créé le :** 25 Octobre 2025, 23:58 UTC  
**Module :** Exchange Selection UI  
**Objectif :** Interface complète multi-exchange 🎛️
