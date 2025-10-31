#!/bin/bash
###############################################################################
# SmartOrder PRO - Démarrage Global
# by MAIGA ABOUBACAR
###############################################################################

echo "🚀 SmartOrder PRO - Starting All Services"
echo "=========================================="

cd /opt/smartorder-pro

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found, copying template..."
    cp .env.template .env
    echo "❌ Please configure .env before starting!"
    exit 1
fi

# Create directories
mkdir -p logs data memory config

# Activate venv
source venv/bin/activate

# Start API
echo "📡 Starting API..."
systemctl restart smartorder-api
sleep 2

# Start Telegram Bot (if configured)
if grep -q "TELEGRAM_BOT_TOKEN=your" .env; then
    echo "⚠️  Telegram not configured, skipping..."
else
    echo "🤖 Starting Telegram Bot..."
    systemctl restart smartorder-telegram 2>/dev/null || \
    nohup python3 telegram/telegram_bot_pro.py > logs/telegram.log 2>&1 &
fi

# Check status
echo ""
echo "✅ Services Status:"
echo "==================="
systemctl status smartorder-api --no-pager -l | head -3
echo ""

# Show endpoints
echo "📍 Endpoints:"
echo "  - API:       http://localhost:8000"
echo "  - Dashboard: https://YOUR_IP/dashboard"
echo "  - Docs:      http://localhost:8000/docs"
echo ""

echo "✅ SmartOrder PRO started successfully!"
echo "📊 View logs: tail -f logs/*.log"
