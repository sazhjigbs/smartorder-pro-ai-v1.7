# 🚀 SmartOrder PRO - Advanced Multi-Exchange Trading Bot

**Professional-grade automated trading system with multi-exchange support, advanced security, and comprehensive monitoring.**

**by MAIGA ABOUBACAR**

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Phases Progress](#phases-progress)
- [Security Best Practices](#security-best-practices)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## 🌟 Overview

SmartOrder PRO is a comprehensive, production-ready cryptocurrency trading bot that supports multiple exchanges (Bybit, Binance, OKX, KuCoin) with intelligent routing, advanced security features, and real-time monitoring capabilities.

### Key Highlights

- ✅ **Multi-Exchange Support**: Trade on Bybit, Binance, OKX, and KuCoin
- 🛡️ **Enterprise Security**: AES-256 encryption, circuit breakers, failover management
- 📊 **Real-Time Monitoring**: WebSocket updates, live dashboards, Telegram alerts
- 🎯 **Smart Routing**: Automatic best exchange selection based on fees, liquidity, and latency
- 📈 **Performance Tracking**: Win rate, Sharpe ratio, drawdown analysis
- 🌐 **Web Interface**: Dashboard and configuration management
- 🔔 **Telegram Integration**: Remote control and analytics reports

---

## 🎯 Features

### Phase 1: Real Trading Integration ✅
- Professional Bybit API integration
- Real order placement and management
- Health monitoring with retry logic
- Security measures (API key encryption)

### Phase 2: Multi-Exchange Support ✅
- Binance, OKX, and KuCoin connectors
- Smart exchange router with automatic selection
- Fee and liquidity optimization
- Latency monitoring

### Phase 3: Security & Monitoring ✅
- AES-256 encryption for API keys
- Master key rotation capability
- Circuit breaker pattern for fail-safe operation
- Failover manager with automatic exchange switching
- Centralized JSON logging with console colors
- Complete documentation suite

### Phase 7: Advanced Dashboard ✅
- Responsive web UI with Chart.js
- Real-time metrics display
- Equity curves and PnL distribution
- Mobile-friendly design

### Phase 8: WebSocket Support ✅
- Real-time price updates
- Live position tracking
- Instant dashboard updates

### Phase 9: Advanced Telegram Bot ✅
- Interactive inline keyboard menus
- Remote trading control (pause/resume)
- Analytics and daily reports
- Position monitoring

### Phase 10: Performance Tracking ✅
- Win rate and profit factor calculation
- Sharpe ratio computation
- Maximum drawdown tracking
- Trade history management

### Phase 11: Web Config Manager ✅
- Browser-based strategy configuration
- Save/load trading parameters
- No file editing required
- Real-time config updates

---

## 🏗️ Architecture

```
smartorder-pro-ai-v1.7/
├── config/                        # Configuration files
│   ├── exchanges.json             # Exchange settings
│   ├── bot_config.json            # Bot parameters
│   └── trading_coins.json         # Trading pairs
├── exchange_connectors/           # Exchange API wrappers
│   ├── bybit_connector.py
│   ├── binance_connector.py
│   ├── okx_connector.py
│   └── kucoin_connector.py
├── core/                          # Core trading logic
│   ├── exchange_router.py         # Smart exchange selection
│   ├── failover_manager.py        # Automatic failover
│   ├── unified_trading_manager.py # Trading orchestration
│   └── bybit_client.py            # Bybit integration
├── monitoring/                    # System monitoring
│   ├── circuit_breaker.py         # Fail-safe mechanism
│   └── exchange_health_monitor.py # Health checks
├── security/                      # Security layer
│   ├── database_encryption.py     # AES-256 encryption
│   └── key_manager.py             # Key management
├── utils/                         # Utilities
│   ├── centralized_logger.py      # Logging system
│   ├── performance_tracker.py     # Trading metrics
│   └── diagnostic.py              # System diagnostics
├── web/                           # Web interface
│   ├── dashboard.html             # Advanced UI
│   ├── websocket_server.py        # Real-time streaming
│   └── config_manager.py          # Web config interface
├── telegram/                      # Telegram integration
│   └── advanced_bot.py            # Bot with analytics
├── tests/                         # Test suite
│   ├── test_e2e.py               # End-to-end tests
│   ├── test_multi_exchange.py    # Exchange tests
│   └── pre_prod_check.py         # Pre-production checks
├── ai_core/                       # AI components
│   ├── ai_guardian.py            # Risk guardian
│   ├── ai_learner.py             # Learning engine
│   └── ai_memory.py              # Trade memory
├── strategies/                    # Trading strategies
│   ├── signal_aggregator.py      # Signal aggregation
│   ├── risk_manager.py           # Risk management
│   └── backtesting.py            # Backtesting engine
└── deploy/                        # Deployment scripts
    ├── auto_deploy_vps.sh        # VPS deployment
    └── *.service                  # Systemd services
```

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- pip package manager
- Virtual environment (recommended)

### Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd smartorder-pro-ai-v1.7
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. **Setup encryption**
```bash
python security/database_encryption.py setup
```

---

## ⚙️ Configuration

### 1. Exchange API Keys

Edit `.env`:
```env
# Bybit
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret

# Binance
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# OKX
OKX_API_KEY=your_api_key
OKX_API_SECRET=your_api_secret
OKX_PASSPHRASE=your_passphrase

# KuCoin
KUCOIN_API_KEY=your_api_key
KUCOIN_API_SECRET=your_api_secret
KUCOIN_PASSPHRASE=your_passphrase

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Security
MASTER_KEY=your_32_byte_master_key
```

### 2. Trading Parameters

Use web interface (http://localhost:5000) or edit `config/bot_config.json`:
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

### 3. Exchange Router Settings

Edit `config/exchanges.json` for exchange priorities and routing logic.

---

## 🚀 Usage

### Start Main Trading Bot
```bash
python core/unified_trading_manager.py
```

### Start Web Dashboard
```bash
python web/config_manager.py
# Visit http://localhost:5000
```

### Start WebSocket Server (Real-time updates)
```bash
python web/websocket_server.py
```

### Start Telegram Bot
```bash
python telegram/advanced_bot.py
```

### View Logs
```bash
tail -f logs/auto_executor.log
```

### Access Dashboards
- **Web Dashboard**: http://localhost:5000 (Config Manager)
- **Trading Dashboard**: Open `web/dashboard.html` in browser
- **WebSocket**: ws://localhost:8765

---

## 📊 Phases Progress

### ✅ Phase 1: Real Trading (100%)
- Bybit integration with real API
- Order placement and management
- Health monitoring
- Retry logic for failed orders

### ✅ Phase 2: Multi-Exchange (100%)
- Binance, OKX, KuCoin connectors
- Smart exchange router
- Fee optimization
- Latency monitoring
- Automatic best exchange selection

### ✅ Phase 3: Security & Monitoring (100%)
- AES-256 encryption for API keys
- Master key rotation
- Circuit breaker pattern
- Failover manager
- Centralized structured logging
- Complete documentation

### ✅ Phase 4-6: Core Features (Partially Complete)
- AI signal integration
- Dashboard UI (existing)
- Multiple deployment options

### ✅ Phase 7: Advanced Dashboard (100%)
- Responsive web UI with Chart.js
- Real-time metrics (equity, PnL, win rate)
- Live trading view with recent trades
- Mobile-responsive design

### ✅ Phase 8: WebSocket Support (100%)
- Real-time data streaming server
- Broadcast to multiple clients
- Live position and price updates

### ✅ Phase 9: Advanced Telegram Bot (100%)
- Interactive inline keyboards
- Remote control (pause/resume/status)
- Analytics commands (/analytics, /report)
- Position monitoring
- Daily trading reports

### ✅ Phase 10: Performance Tracking (100%)
- Win rate and profit factor calculation
- Sharpe ratio and max drawdown
- Trade history with timestamps
- Best/worst trade tracking
- Save/load performance data

### ✅ Phase 11: Web Config Manager (100%)
- Flask-based web interface
- Browser-based strategy configuration
- Save/load trading parameters
- API endpoints for config management
- No manual file editing needed

### 🔄 Phase 12: Final Documentation (In Progress)
- ✅ Comprehensive README
- ⏳ API documentation
- ⏳ Changelog
- ⏳ Contribution guidelines

**Overall Progress: 9/12 Phases Complete (75%)**

---

## 🔒 Security Best Practices

### API Key Management
1. **Never commit API keys** to version control
2. Use `.env` file (included in `.gitignore`)
3. Enable **IP whitelisting** on exchange accounts
4. Use **read-only keys** for monitoring, separate keys for trading

### Master Key Security
```bash
# Generate secure master key
python -c "import secrets; print(secrets.token_hex(32))"

# Rotate master key regularly
python security/key_manager.py --rotate
```

### Circuit Breaker
The circuit breaker protects against cascading failures:
- **Failure Threshold**: 5 consecutive failures
- **Recovery Timeout**: 300 seconds
- **Half-Open Attempts**: 2 test attempts before full recovery

### Failover Configuration
- Set conservative health thresholds
- Test failover before production
- Monitor failover events in logs
- Review `core/failover_manager.py` settings

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Suite
```bash
pytest tests/test_e2e.py -v
pytest tests/test_multi_exchange.py -v
```

### Pre-Production Check
```bash
python tests/pre_prod_check.py
```

### Integration Tests
```bash
pytest tests/ --testnet
```

---

## 🌐 Deployment

### VPS Deployment (Ubuntu 20.04+)

1. **Install dependencies**
```bash
sudo apt update
sudo apt install python3.9 python3-pip git -y
```

2. **Clone and setup**
```bash
git clone <repository-url>
cd smartorder-pro-ai-v1.7
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Setup systemd service**
```bash
sudo cp deploy/smartorder-trading.service /etc/systemd/system/
sudo systemctl enable smartorder-trading
sudo systemctl start smartorder-trading
sudo systemctl status smartorder-trading
```

4. **Enable auto-deployment**
```bash
./deploy/auto_deploy_vps.sh
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "core/unified_trading_manager.py"]
```

```bash
docker build -t smartorder-pro .
docker run -d --env-file .env --name smartorder smartorder-pro
```

---

## 📈 Monitoring

### Dashboard Access
- **Config Manager**: http://localhost:5000
- **Live Dashboard**: Open `web/dashboard.html`
- **WebSocket**: ws://localhost:8765
- **Telegram Bot**: @YourBotUsername

### Log Monitoring
```bash
# Real-time logs
tail -f logs/auto_executor.log

# Error logs
grep ERROR logs/*.log

# Performance metrics
python utils/performance_tracker.py
```

### Health Checks
```bash
# Manual health check
python monitoring/exchange_health_monitor.py

# Full system diagnostic
python utils/diagnostic.py

# Automated monitoring (cron)
*/5 * * * * /path/to/venv/bin/python /path/to/monitoring/exchange_health_monitor.py
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Connection Errors**
```
Solution: Check internet connection, verify API keys, check exchange status
Log: logs/auto_executor.log
```

**2. Authentication Failed**
```
Solution: Verify API keys in .env, check IP whitelist, ensure correct permissions
```

**3. Circuit Breaker Triggered**
```
Solution: Check logs for failures, verify exchange health, wait for recovery
Monitor: logs/auto_executor.log for "Circuit Breaker" messages
```

**4. WebSocket Disconnections**
```
Solution: Check network stability, review websocket_server.py logs
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python core/unified_trading_manager.py
```

### Run Full Diagnostic
```bash
python utils/diagnostic.py
./tools/diagnostic_smartorder.sh
```

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## ⚠️ Disclaimer

**This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. Past performance is not indicative of future results. Use at your own risk.**

---

## 🙏 Acknowledgments

- CCXT library for exchange integration
- Chart.js for visualization
- python-telegram-bot for Telegram integration
- Flask for web interface
- The open-source trading community

---

**Made with ❤️ by MAIGA ABOUBACAR**

*Last Updated: 2024 - v1.9-FINAL with Phases 7-11 Complete*

---
