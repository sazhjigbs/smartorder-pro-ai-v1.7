#!/bin/bash
################################################################################
# 🛑 SAFELOGIC SmartOrder PRO - Script d'Arrêt
# by MAIGA ABOUBACAR
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="/opt/smartorder-pro"
DATA_DIR="$PROJECT_ROOT/data"
DASHBOARD_PID_FILE="$DATA_DIR/dashboard.pid"

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo ""
echo -e "${RED}🛑 Arrêt du bot SmartOrder PRO...${NC}"
echo ""

# Arrêter dashboard
if [ -f "$DASHBOARD_PID_FILE" ]; then
    PID=$(cat "$DASHBOARD_PID_FILE")
    log_info "Arrêt du dashboard (PID: $PID)..."
    
    if kill -0 $PID 2>/dev/null; then
        kill -15 $PID
        sleep 2
        
        # Force kill si toujours actif
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
            log_success "Dashboard arrêté (force)"
        else
            log_success "Dashboard arrêté"
        fi
    else
        log_info "Dashboard déjà arrêté"
    fi
    
    rm -f "$DASHBOARD_PID_FILE"
else
    log_info "Pas de PID file trouvé"
fi

# Arrêter tous les processus uvicorn
UVICORN_PIDS=$(pgrep -f "uvicorn.*main_unified" || true)
if [ ! -z "$UVICORN_PIDS" ]; then
    log_info "Arrêt des processus uvicorn restants..."
    echo "$UVICORN_PIDS" | xargs kill -9 2>/dev/null || true
    log_success "Processus uvicorn arrêtés"
fi

echo ""
log_success "Bot SmartOrder PRO arrêté !"
echo ""
