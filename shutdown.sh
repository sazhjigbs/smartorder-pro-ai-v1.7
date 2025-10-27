#!/bin/bash
# SmartOrder PRO - Shutdown Script

echo "Stopping SmartOrder PRO..."

# Stop dashboard
if [ -f .dashboard.pid ]; then
    PID=$(cat .dashboard.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "[OK] Dashboard stopped (PID: $PID)"
    fi
    rm .dashboard.pid
fi

echo "SmartOrder PRO stopped"
