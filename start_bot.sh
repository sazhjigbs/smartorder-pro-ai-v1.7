#!/bin/bash
################################################################################
# 🚀 SAFELOGIC SmartOrder PRO - Script de Démarrage Automatique
# by MAIGA ABOUBACAR
################################################################################
# 
# Usage:
#   chmod +x start_bot.sh
#   ./start_bot.sh
#
# Ce script démarre tous les composants nécessaires:
# 1. Vérification environnement
# 2. Initialisation bot state
# 3. Dashboard FastAPI (port 8555)
# 4. Services AI (systemd)
# 5. Health checks
#
################################################################################

set -e  # Exit on error

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/opt/smartorder-pro"
VENV_PATH="$PROJECT_ROOT/venv"
DASHBOARD_PORT=8555
LOG_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║    🚀 SAFELOGIC SmartOrder PRO - Startup Script            ║"
    echo "║    by MAIGA ABOUBACAR                                        ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_requirements() {
    log_info "Vérification des prérequis..."
    
    # Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 non trouvé"
        exit 1
    fi
    log_success "Python 3: $(python3 --version)"
    
    # Pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 non trouvé"
        exit 1
    fi
    log_success "pip3 installé"
    
    # Systemctl (pour services AI)
    if ! command -v systemctl &> /dev/null; then
        log_warning "systemctl non trouvé - Les services AI ne seront pas démarrés"
    fi
}

check_env_file() {
    log_info "Vérification du fichier .env..."
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error "Fichier .env introuvable: $PROJECT_ROOT/.env"
        log_warning "Créez le fichier .env avec vos clés API:"
        echo ""
        echo "BYBIT_API_KEY=your_key"
        echo "BYBIT_API_SECRET=your_secret"
        echo "TELEGRAM_BOT_TOKEN=your_token"
        echo "TELEGRAM_CHAT_ID=your_chat_id"
        exit 1
    fi
    
    log_success "Fichier .env trouvé"
    
    # Vérifier que les clés essentielles sont présentes
    if ! grep -q "BYBIT_API_KEY" "$PROJECT_ROOT/.env"; then
        log_error "BYBIT_API_KEY manquant dans .env"
        exit 1
    fi
    
    log_success "Variables d'environnement validées"
}

create_directories() {
    log_info "Création des répertoires nécessaires..."
    
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    
    log_success "Répertoires créés: logs/, data/"
}

init_bot_state() {
    log_info "Initialisation du bot state manager..."
    
    cd "$PROJECT_ROOT"
    
    # Charger virtualenv si existe
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi
    
    # Initialiser le state manager
    python3 -c "from core.bot_state_manager import get_state_manager; mgr = get_state_manager(); print('State:', mgr.get_status())" 2>&1 | tee -a "$LOG_DIR/startup.log"
    
    if [ $? -eq 0 ]; then
        log_success "Bot state initialisé"
    else
        log_warning "Erreur lors de l'initialisation du state (continuant quand même...)"
    fi
}

start_dashboard() {
    log_info "Démarrage du dashboard FastAPI (port $DASHBOARD_PORT)..."
    
    cd "$PROJECT_ROOT"
    
    # Vérifier si déjà lancé
    if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Le dashboard est déjà en cours d'exécution sur le port $DASHBOARD_PORT"
        PID=$(lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t)
        log_info "PID actuel: $PID"
        read -p "Voulez-vous le redémarrer ? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill -9 $PID
            log_success "Ancien processus arrêté"
        else
            log_info "Utilisation du dashboard existant"
            return
        fi
    fi
    
    # Charger virtualenv si existe
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi
    
    # Démarrer dashboard en background
    nohup python3 -m uvicorn web.portal_v5_pro.main_unified:app \
        --host 0.0.0.0 \
        --port $DASHBOARD_PORT \
        --log-level info \
        > "$LOG_DIR/dashboard.log" 2>&1 &
    
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > "$DATA_DIR/dashboard.pid"
    
    # Attendre que le dashboard démarre
    log_info "Attente du démarrage du dashboard..."
    for i in {1..10}; do
        if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_success "Dashboard démarré (PID: $DASHBOARD_PID)"
            return
        fi
        sleep 1
    done
    
    log_error "Le dashboard n'a pas pu démarrer"
    log_info "Vérifiez les logs: tail -f $LOG_DIR/dashboard.log"
}

check_ai_services() {
    log_info "Vérification des services AI (systemd)..."
    
    if ! command -v systemctl &> /dev/null; then
        log_warning "systemctl non disponible - Services AI non vérifiés"
        return
    fi
    
    # Liste des services AI
    AI_SERVICES=(
        "smartorder-fusion-ai.service"
        "smartorder-genetic.service"
        "smartorder-behavior.service"
    )
    
    for service in "${AI_SERVICES[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service: Running"
        else
            log_warning "$service: Stopped"
            log_info "Pour démarrer: sudo systemctl start $service"
        fi
    done
}

display_summary() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Bot SmartOrder PRO démarré avec succès !${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "📊 Dashboard:   ${YELLOW}http://$(hostname -I | awk '{print $1}'):$DASHBOARD_PORT${NC}"
    echo -e "📁 Logs:        ${YELLOW}$LOG_DIR/${NC}"
    echo -e "💾 Data:        ${YELLOW}$DATA_DIR/${NC}"
    echo ""
    echo -e "${CYAN}Commandes utiles:${NC}"
    echo -e "  - Voir logs dashboard:     ${YELLOW}tail -f $LOG_DIR/dashboard.log${NC}"
    echo -e "  - Voir logs bot:           ${YELLOW}tail -f $LOG_DIR/bot.log${NC}"
    echo -e "  - Arrêter dashboard:       ${YELLOW}kill \$(cat $DATA_DIR/dashboard.pid)${NC}"
    echo -e "  - État bot:                ${YELLOW}python3 -c 'from core.bot_state_manager import get_state_manager; print(get_state_manager().get_full_state())'${NC}"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

health_check() {
    log_info "Health check des composants..."
    
    # Check dashboard
    if curl -s "http://localhost:$DASHBOARD_PORT/api/ping" >/dev/null 2>&1; then
        log_success "Dashboard: Healthy"
    else
        log_warning "Dashboard: Not responding"
    fi
    
    # Check bot state file
    if [ -f "$DATA_DIR/bot_state.json" ]; then
        log_success "Bot state: OK"
    else
        log_warning "Bot state: Fichier non trouvé"
    fi
}

################################################################################
# Main
################################################################################

main() {
    print_header
    
    # Étape 1: Prérequis
    check_requirements
    
    # Étape 2: Environnement
    check_env_file
    
    # Étape 3: Répertoires
    create_directories
    
    # Étape 4: Init bot state
    init_bot_state
    
    # Étape 5: Dashboard
    start_dashboard
    
    # Étape 6: Services AI
    check_ai_services
    
    # Étape 7: Health check
    sleep 2
    health_check
    
    # Étape 8: Summary
    display_summary
    
    log_success "Startup script terminé !"
}

# Cleanup on exit
cleanup() {
    log_info "Nettoyage..."
}

trap cleanup EXIT

# Run main
main "$@"
