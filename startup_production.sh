#!/bin/bash
# SmartOrder PRO - Production Startup Script
# Author: MAIGA ABOUBACAR

echo "=========================================="
echo "SmartOrder PRO - Starting Production Mode"
echo "=========================================="

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "[OK] Environment loaded"
else
    echo "[ERROR] .env not found!"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
    exit 1
fi

# Create required directories
mkdir -p logs data

# Check dependencies
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn, pybit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Run pre-production checks
echo "Running pre-production checks..."
python3 utils/diagnostic.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Pre-production checks failed!"
    echo "Fix errors before starting production"
    exit 1
fi

# Start dashboard
echo "Starting dashboard on port $DASHBOARD_PORT..."
nohup python3 dashboard/main_unified.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > .dashboard.pid
echo "[OK] Dashboard started (PID: $DASHBOARD_PID)"

# Wait and verify
sleep 3
if ps -p $DASHBOARD_PID > /dev/null; then
    echo "[OK] Dashboard is running"
    echo ""
    echo "=========================================="
    echo "SmartOrder PRO is LIVE!"
    echo "=========================================="
    echo "Dashboard: http://localhost:$DASHBOARD_PORT"
    echo "Logs: tail -f logs/dashboard.log"
    echo "Stop: ./shutdown.sh"
    echo "=========================================="
else
    echo "[ERROR] Dashboard failed to start"
    cat logs/dashboard.log
    exit 1
fi
