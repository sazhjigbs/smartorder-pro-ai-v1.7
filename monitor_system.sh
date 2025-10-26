#!/bin/bash
#################################################################
# 🔍 SAFELOGIC SmartOrder PRO - System Monitor
# Vérifie tous les services et envoie des alertes
#################################################################

SCRIPT_DIR="/opt/smartorder-pro"
LOG_FILE="$SCRIPT_DIR/logs/monitor.log"
ALERT_FILE="$SCRIPT_DIR/logs/alerts.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Thresholds
CPU_THRESHOLD=80
RAM_THRESHOLD=85
DISK_THRESHOLD=90

# Services to monitor
SERVICES=(
    "smartorder-portal-v5"
)

# Ports to monitor
PORTS=(
    8555
    8191
)

echo "========================================="
echo "🔍 SmartOrder PRO - System Monitor"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

# Function: Check service status
check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✅ $service: RUNNING${NC}"
        return 0
    else
        echo -e "${RED}❌ $service: STOPPED${NC}"
        echo "[$(date)] ALERT: $service is STOPPED" >> "$ALERT_FILE"
        return 1
    fi
}

# Function: Check port
check_port() {
    local port=$1
    if ss -tulnp | grep -q ":$port "; then
        echo -e "${GREEN}✅ Port $port: LISTENING${NC}"
        return 0
    else
        echo -e "${RED}❌ Port $port: NOT LISTENING${NC}"
        echo "[$(date)] ALERT: Port $port not listening" >> "$ALERT_FILE"
        return 1
    fi
}

# Function: Check resource usage
check_resources() {
    local cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d'.' -f1)
    local ram=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    local disk=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    
    echo ""
    echo "📊 System Resources:"
    
    # CPU
    if [ "$cpu" -gt "$CPU_THRESHOLD" ]; then
        echo -e "${RED}  CPU: ${cpu}% (⚠️ HIGH)${NC}"
        echo "[$(date)] ALERT: CPU usage at ${cpu}%" >> "$ALERT_FILE"
    else
        echo -e "${GREEN}  CPU: ${cpu}%${NC}"
    fi
    
    # RAM
    if [ "$ram" -gt "$RAM_THRESHOLD" ]; then
        echo -e "${RED}  RAM: ${ram}% (⚠️ HIGH)${NC}"
        echo "[$(date)] ALERT: RAM usage at ${ram}%" >> "$ALERT_FILE"
    else
        echo -e "${GREEN}  RAM: ${ram}%${NC}"
    fi
    
    # Disk
    if [ "$disk" -gt "$DISK_THRESHOLD" ]; then
        echo -e "${RED}  DISK: ${disk}% (⚠️ HIGH)${NC}"
        echo "[$(date)] ALERT: Disk usage at ${disk}%" >> "$ALERT_FILE"
    else
        echo -e "${GREEN}  DISK: ${disk}%${NC}"
    fi
}

# Function: Check API health
check_api() {
    local url=$1
    local name=$2
    
    if curl -sf "$url" > /dev/null; then
        echo -e "${GREEN}✅ $name API: HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ $name API: UNHEALTHY${NC}"
        echo "[$(date)] ALERT: $name API unhealthy" >> "$ALERT_FILE"
        return 1
    fi
}

# Main monitoring
echo "🔧 Checking Services:"
for service in "${SERVICES[@]}"; do
    check_service "$service"
done

echo ""
echo "🔌 Checking Ports:"
for port in "${PORTS[@]}"; do
    check_port "$port"
done

check_resources

echo ""
echo "🌐 Checking APIs:"
check_api "http://localhost:8555/health" "Dashboard"
check_api "http://localhost:8555/api/execution/health" "Execution Engine"
check_api "http://localhost:8555/api/pnl/summary" "PNL Live"

echo ""
echo "========================================="

# Count alerts
ALERT_COUNT=$(wc -l < "$ALERT_FILE" 2>/dev/null || echo 0)
if [ "$ALERT_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Total alerts: $ALERT_COUNT${NC}"
    echo "Check $ALERT_FILE for details"
else
    echo -e "${GREEN}✅ No alerts${NC}"
fi

echo "========================================="
echo ""

# Log to file
echo "[$(date)] Monitor check completed" >> "$LOG_FILE"
