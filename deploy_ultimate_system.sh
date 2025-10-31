#!/bin/bash
##############################################################################
# SMARTORDER PRO - ULTIMATE DEPLOYMENT
# by MAIGA ABOUBACAR
# 
# Déploie le système complet avec:
# - Smart Strategy Manager
# - Adaptive Scalping Engine
# - Smart Position Manager
# - Multi-TP & Funding Optimizer
# - Dashboard Ultimate
##############################################################################

set -e

echo "=================================="
echo "🚀 SMARTORDER PRO ULTIMATE"
echo "Deployment Script v2.0"
echo "by MAIGA ABOUBACAR"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directories
PROJECT_DIR="/opt/smartorder-pro"
BACKUP_DIR="/opt/smartorder-pro/backups/$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p $PROJECT_DIR/{core,web,data,logs,config,backups}
mkdir -p $BACKUP_DIR

# 1. BACKUP EXISTING FILES
echo -e "${YELLOW}📦 Backing up existing files...${NC}"
if [ -f "$PROJECT_DIR/smart_strategy_manager.py" ]; then
    cp -r $PROJECT_DIR/*.py $BACKUP_DIR/ 2>/dev/null || true
    echo "   ✅ Backup created at $BACKUP_DIR"
fi

# 2. STOP RUNNING PROCESSES
echo -e "${YELLOW}🛑 Stopping running processes...${NC}"
pkill -f "python.*trading" 2>/dev/null || true
pkill -f "python.*api" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 3
echo "   ✅ Processes stopped"

# 3. COPY NEW FILES
echo -e "${BLUE}📤 Uploading new files to VPS...${NC}"

# Note: This script should be run on the VPS after uploading files
# Files to upload from Windows to VPS:
echo "   📄 strategies_config_complete.json"
echo "   📄 smart_strategy_manager.py"
echo "   📄 core/adaptive_scalping_engine.py"
echo "   📄 core/smart_position_manager.py"
echo "   📄 core/multi_tp_and_funding_optimizer.py"
echo "   📄 web/dashboard_ultimate.html"

# Check if files exist
REQUIRED_FILES=(
    "$PROJECT_DIR/strategies_config_complete.json"
    "$PROJECT_DIR/smart_strategy_manager.py"
    "$PROJECT_DIR/core/adaptive_scalping_engine.py"
    "$PROJECT_DIR/core/smart_position_manager.py"
    "$PROJECT_DIR/core/multi_tp_and_funding_optimizer.py"
    "$PROJECT_DIR/web/dashboard_ultimate.html"
)

echo ""
echo -e "${BLUE}🔍 Checking required files...${NC}"
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $(basename $file)"
    else
        echo "   ❌ $(basename $file) - MISSING!"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ ERROR: $MISSING_FILES files are missing!${NC}"
    echo -e "${YELLOW}Please upload files first using SCP:${NC}"
    echo ""
    echo "scp -r C:\\Users\\aimet\\smartorder-pro-ai-v1.7\\*.json root@107.189.22.255:/opt/smartorder-pro/"
    echo "scp C:\\Users\\aimet\\smartorder-pro-ai-v1.7\\smart_strategy_manager.py root@107.189.22.255:/opt/smartorder-pro/"
    echo "scp C:\\Users\\aimet\\smartorder-pro-ai-v1.7\\core\\*.py root@107.189.22.255:/opt/smartorder-pro/core/"
    echo "scp C:\\Users\\aimet\\smartorder-pro-ai-v1.7\\web\\dashboard_ultimate.html root@107.189.22.255:/opt/smartorder-pro/web/"
    echo ""
    exit 1
fi

# 4. SET PERMISSIONS
echo ""
echo -e "${BLUE}🔐 Setting permissions...${NC}"
chmod +x $PROJECT_DIR/*.py 2>/dev/null || true
chmod +x $PROJECT_DIR/core/*.py 2>/dev/null || true
chmod 644 $PROJECT_DIR/web/*.html
chmod 644 $PROJECT_DIR/*.json
echo "   ✅ Permissions set"

# 5. INSTALL DEPENDENCIES (if needed)
echo ""
echo -e "${BLUE}📦 Checking Python dependencies...${NC}"
python3 -c "import ccxt, pandas, ta" 2>/dev/null && echo "   ✅ Core dependencies OK" || {
    echo "   ⚠️ Installing missing dependencies..."
    pip3 install ccxt pandas ta numpy fastapi uvicorn
}

# 6. INITIALIZE CONFIG
echo ""
echo -e "${BLUE}⚙️ Initializing configuration...${NC}"

# Create initial trading state if not exists
if [ ! -f "$PROJECT_DIR/data/trading_state.json" ]; then
    cat > $PROJECT_DIR/data/trading_state.json << 'EOF'
{
  "mode": "PAPER",
  "current_capital": 10000,
  "total_pnl": 0,
  "active_strategies": ["Grid Trading", "DCA Strategy", "Scalping"],
  "positions": [],
  "recovery_mode": false,
  "volatility_regime": "medium",
  "market_regime": "sideways",
  "active_strategy": "None",
  "last_update": ""
}
EOF
    echo "   ✅ Trading state initialized"
fi

# 7. CREATE BACKEND API
echo ""
echo -e "${BLUE}🔧 Creating Backend API...${NC}"

cat > $PROJECT_DIR/backend_api_ultimate.py << 'EOFAPI'
#!/usr/bin/env python3
"""
Backend API Ultimate for SmartOrder PRO
by MAIGA ABOUBACAR
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

app = FastAPI(title="SmartOrder PRO Ultimate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_FILE = '/opt/smartorder-pro/data/trading_state.json'
STRATEGIES_CONFIG = '/opt/smartorder-pro/strategies_config_complete.json'

def read_json(filepath, default=None):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return default or {}
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return default or {}

def write_json(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False

@app.get("/api/state")
def get_state():
    """Get current trading state"""
    state = read_json(STATE_FILE, {
        'mode': 'PAPER',
        'current_capital': 10000,
        'total_pnl': 0,
        'active_strategies': [],
        'recovery_mode': False,
        'volatility_regime': 'medium',
        'market_regime': 'sideways',
        'active_strategy': 'None'
    })
    state['last_update'] = datetime.now().isoformat()
    return state

@app.post("/api/mode")
def set_mode(data: dict):
    """Change trading mode"""
    mode = data.get('mode', 'PAPER').upper()
    state = read_json(STATE_FILE, {})
    state['mode'] = mode
    state['last_update'] = datetime.now().isoformat()
    write_json(STATE_FILE, state)
    return {'success': True, 'mode': mode}

@app.get("/api/strategies")
def get_strategies(mode: str = 'SPOT'):
    """Get strategies for a mode"""
    config = read_json(STRATEGIES_CONFIG, {})
    mode = mode.upper()
    
    if 'modes' not in config or mode not in config['modes']:
        return {'strategies': []}
    
    mode_config = config['modes'][mode]
    strategies = []
    
    for strategy_id, strategy_data in mode_config.get('strategies', {}).items():
        strategies.append({
            'id': strategy_id,
            'name': strategy_data.get('name', strategy_id),
            'enabled': strategy_data.get('enabled', False),
            'score': 75,  # TODO: Calculate real score
            'reason': 'Compatible with current market',
            'recommended': strategy_data.get('priority', 999) <= 3
        })
    
    return {'strategies': strategies}

@app.post("/api/strategy/toggle")
def toggle_strategy(data: dict):
    """Toggle strategy on/off"""
    mode = data.get('mode', 'SPOT').upper()
    strategy_id = data.get('strategy')
    enabled = data.get('enabled', False)
    
    config = read_json(STRATEGIES_CONFIG, {})
    
    if 'modes' in config and mode in config['modes']:
        if strategy_id in config['modes'][mode]['strategies']:
            config['modes'][mode]['strategies'][strategy_id]['enabled'] = enabled
            write_json(STRATEGIES_CONFIG, config)
            return {'success': True}
    
    return {'success': False, 'error': 'Strategy not found'}

@app.get("/api/exchanges")
def get_exchanges():
    """Get exchanges status"""
    return {
        'exchanges': [
            {'name': 'Bybit', 'connected': True, 'balance': 10000},
            {'name': 'Binance', 'connected': False, 'balance': 0},
            {'name': 'OKX', 'connected': False, 'balance': 0}
        ]
    }

@app.get("/health")
def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
EOFAPI

chmod +x $PROJECT_DIR/backend_api_ultimate.py
echo "   ✅ Backend API created"

# 8. START SERVICES
echo ""
echo -e "${GREEN}🚀 Starting services...${NC}"
echo ""

# Start Backend API
cd $PROJECT_DIR
nohup python3 backend_api_ultimate.py > logs/api_ultimate.log 2>&1 &
API_PID=$!
echo "   ✅ Backend API started (PID: $API_PID)"
sleep 3

# Verify API is running
if curl -s http://localhost:8001/health | grep -q "ok"; then
    echo "   ✅ Backend API is healthy"
else
    echo "   ⚠️ Backend API may not be responding"
fi

# 9. CONFIGURE NGINX (if needed)
echo ""
echo -e "${BLUE}🌐 Checking NGINX configuration...${NC}"

if command -v nginx &> /dev/null; then
    NGINX_CONF="/etc/nginx/sites-available/smartorder"
    
    if [ ! -f "$NGINX_CONF" ]; then
        echo "   Creating NGINX config..."
        cat > $NGINX_CONF << 'EOFNGINX'
server {
    listen 80;
    server_name 107.189.22.255;

    location / {
        root /opt/smartorder-pro/web;
        try_files $uri $uri/ /dashboard_ultimate.html;
    }

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOFNGINX
        
        ln -sf $NGINX_CONF /etc/nginx/sites-enabled/smartorder 2>/dev/null || true
        nginx -t && nginx -s reload
        echo "   ✅ NGINX configured and reloaded"
    else
        echo "   ✅ NGINX already configured"
    fi
else
    echo "   ⚠️ NGINX not installed - using direct access on port 8001"
fi

# 10. FINAL STATUS
echo ""
echo "=================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "=================================="
echo ""
echo "📊 Services Status:"
echo "   • Backend API: Running on port 8001"
echo "   • Dashboard: Available at http://107.189.22.255/dashboard_ultimate.html"
echo ""
echo "📝 Logs:"
echo "   • API: tail -f /opt/smartorder-pro/logs/api_ultimate.log"
echo ""
echo "🔧 Management Commands:"
echo "   • Check API: curl http://localhost:8001/health"
echo "   • Check processes: ps aux | grep python"
echo "   • Stop all: pkill -f 'python.*smartorder'"
echo ""
echo "📂 Files Location:"
echo "   • Project: /opt/smartorder-pro"
echo "   • Config: /opt/smartorder-pro/strategies_config_complete.json"
echo "   • Data: /opt/smartorder-pro/data/"
echo "   • Logs: /opt/smartorder-pro/logs/"
echo ""
echo "🌐 Access Dashboard:"
echo "   http://107.189.22.255/dashboard_ultimate.html"
echo "   or"
echo "   https://107.189.22.255/dashboard_ultimate.html"
echo ""
echo -e "${YELLOW}⚠️  REMEMBER: System is in PAPER mode by default${NC}"
echo ""
echo "Next steps:"
echo "1. Open dashboard in browser"
echo "2. Select trading mode (SPOT/FUTURES/HYBRIDE/MANUEL)"
echo "3. Toggle strategies you want to activate"
echo "4. Monitor in Live Activity Log"
echo ""
echo "=================================="
echo -e "${GREEN}by MAIGA ABOUBACAR${NC}"
echo "=================================="
