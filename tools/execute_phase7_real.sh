#!/bin/bash
################################################################################
# PHASE 7 - PASSAGE MODE REAL
# SmartOrder PRO AI v2.4
# ⚠️  ATTENTION: Ce script active le trading avec de l'argent réel
# by MAIGA ABOUBAKR - SAFELOGIC
################################################################################

set -e

# Configuration
BASE_PATH="/opt/smartorder-pro"
LOGS_PATH="$BASE_PATH/logs"
BACKUP_PATH="/opt/smartorder-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

################################################################################
# Pre-flight Checks for Phase 7
################################################################################

preflight_phase7() {
    log "🔍 Phase 7 Pre-flight Checks..."
    
    # Check Phase 6 completed
    if [ ! -f "$LOGS_PATH/PHASE_6_SUCCESS.log" ]; then
        error "Phase 6 not completed. Cannot proceed to Phase 7."
        exit 1
    fi
    
    # Check if 24h elapsed since Phase 6
    phase6_time=$(stat -c %Y "$LOGS_PATH/PHASE_6_SUCCESS.log" 2>/dev/null || echo 0)
    current_time=$(date +%s)
    elapsed=$((current_time - phase6_time))
    hours_elapsed=$((elapsed / 3600))
    
    if [ $hours_elapsed -lt 24 ]; then
        warning "Only $hours_elapsed hours elapsed since Phase 6"
        warning "Recommended: Wait 24h minimum for PAPER testing"
        echo ""
        read -p "Continue anyway? (type 'YES' to proceed): " confirm
        if [ "$confirm" != "YES" ]; then
            error "Phase 7 cancelled by user"
            exit 1
        fi
    else
        success "$hours_elapsed hours of PAPER testing completed"
    fi
    
    # Check API keys configured
    log "Checking API keys configuration..."
    if [ -f "$BASE_PATH/.env" ]; then
        if grep -q "your_api_key_here" "$BASE_PATH/.env"; then
            error "API keys not configured in .env"
            error "Please update BYBIT_API_KEY and BYBIT_API_SECRET"
            exit 1
        fi
        success "API keys configured"
    else
        error ".env file not found"
        exit 1
    fi
    
    # Check system status
    log "Checking system status..."
    if ! systemctl is-active --quiet smartorder-api-v24.service; then
        error "smartorder-api-v24.service is not running"
        exit 1
    fi
    success "API service running"
    
    # Test API health
    if ! curl -sf http://localhost:8091/api/health > /dev/null; then
        error "API health check failed"
        exit 1
    fi
    success "API health OK"
}

################################################################################
# Manual Confirmation
################################################################################

confirm_phase7() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  PHASE 7 - PASSAGE MODE REAL                              ║"
    echo "║  ⚠️  TRADING WITH REAL MONEY                                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    warning "This will switch from PAPER to REAL trading mode"
    warning "Real money will be at risk"
    echo ""
    echo "Prerequisites checklist:"
    echo "  [ ] 24h+ successful PAPER testing"
    echo "  [ ] Real API keys configured and tested"
    echo "  [ ] Guardian risk limits validated"
    echo "  [ ] Telegram notifications active"
    echo "  [ ] Backup created"
    echo "  [ ] Manual approval obtained"
    echo ""
    
    read -p "Are ALL prerequisites met? (type 'I CONFIRM' to proceed): " final_confirm
    
    if [ "$final_confirm" != "I CONFIRM" ]; then
        error "Phase 7 cancelled - confirmation not received"
        exit 1
    fi
    
    echo ""
    log "Confirmation received. Proceeding with Phase 7..."
}

################################################################################
# Execute Phase 7
################################################################################

execute_phase7() {
    log "💰 Executing Phase 7 - Real Mode Activation"
    
    cd "$BASE_PATH"
    
    # Create backup before switching
    log "Creating safety backup..."
    tar -czf "$BACKUP_PATH/pre_real_backup_$TIMESTAMP.tar.gz" \
        --exclude='venv' \
        --exclude='logs/*.log' \
        . 2>/dev/null || true
    success "Backup created: pre_real_backup_$TIMESTAMP.tar.gz"
    
    # Backup current .env
    cp "$BASE_PATH/.env" "$BASE_PATH/.env.backup_$TIMESTAMP"
    success "Current .env backed up"
    
    # Update .env to REAL mode
    log "Switching to REAL mode..."
    sed -i 's/MODE=paper/MODE=real/g' "$BASE_PATH/.env"
    sed -i 's/MODE=PAPER/MODE=real/g' "$BASE_PATH/.env"
    
    # Verify change
    if grep -q "MODE=real" "$BASE_PATH/.env"; then
        success "Mode switched to REAL in .env"
    else
        error "Failed to update .env"
        exit 1
    fi
    
    # Update Guardian config for REAL mode (more conservative)
    log "Updating Guardian config for REAL mode..."
    sed -i 's/MAX_DAILY_LOSS_PCT=5.0/MAX_DAILY_LOSS_PCT=3.0/g' "$BASE_PATH/.env"
    sed -i 's/MAX_POSITION_SIZE_PCT=10.0/MAX_POSITION_SIZE_PCT=5.0/g' "$BASE_PATH/.env"
    success "Guardian limits updated (more conservative)"
    
    # Restart services
    log "Restarting services..."
    systemctl restart smartorder-api-v24.service
    sleep 5
    
    # Verify service restarted
    if systemctl is-active --quiet smartorder-api-v24.service; then
        success "API service restarted successfully"
    else
        error "Service failed to restart"
        error "Rolling back..."
        cp "$BASE_PATH/.env.backup_$TIMESTAMP" "$BASE_PATH/.env"
        systemctl restart smartorder-api-v24.service
        exit 1
    fi
    
    # Test API in REAL mode
    log "Testing API in REAL mode..."
    sleep 3
    
    api_status=$(curl -s http://localhost:8091/api/status | grep -o '"mode":"[^"]*"' || echo "")
    if echo "$api_status" | grep -q "real"; then
        success "API confirmed running in REAL mode"
    else
        warning "Could not confirm REAL mode via API"
    fi
    
    # Create Phase 7 success marker
    cat > "$LOGS_PATH/PHASE_7_SUCCESS.log" << EOF
PHASE 7 - SUCCESS
Timestamp: $(date -Iseconds)
Mode: REAL
Activated by: execute_phase7_real.sh
Guardian Limits: Daily Loss 3%, Position Size 5%
Backup: pre_real_backup_$TIMESTAMP.tar.gz
EOF
    
    success "Phase 7 completed successfully"
}

################################################################################
# Post-activation monitoring
################################################################################

post_activation_checks() {
    log "📊 Post-activation checks..."
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🎯 REAL MODE ACTIVATED                                        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    success "System now running in REAL trading mode"
    success "Guardian limits: Daily Loss 3%, Position Size 5%"
    success "Backup available: $BACKUP_PATH/pre_real_backup_$TIMESTAMP.tar.gz"
    
    echo ""
    warning "⚠️  IMPORTANT - IMMEDIATE ACTIONS:"
    echo "  1. Monitor logs continuously: tail -f $LOGS_PATH/api_v24.log"
    echo "  2. Watch first trades carefully"
    echo "  3. Verify Telegram notifications working"
    echo "  4. Check Guardian is active"
    echo "  5. Monitor exchange balances"
    echo ""
    
    echo "Monitoring commands:"
    echo "  • System status: $BASE_PATH/tools/monitor.sh"
    echo "  • Live logs: tail -f $LOGS_PATH/api_v24.log"
    echo "  • Service status: systemctl status smartorder-api-v24"
    echo "  • Emergency stop: systemctl stop smartorder-api-v24"
    echo ""
    
    echo "Rollback procedure (if needed):"
    echo "  1. systemctl stop smartorder-api-v24"
    echo "  2. cp $BASE_PATH/.env.backup_$TIMESTAMP $BASE_PATH/.env"
    echo "  3. systemctl start smartorder-api-v24"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  SmartOrder PRO AI v2.4 - PHASE 7 ACTIVATION                  ║"
    echo "║  by MAIGA ABOUBAKR - SAFELOGIC                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    preflight_phase7
    echo ""
    
    confirm_phase7
    echo ""
    
    execute_phase7
    echo ""
    
    post_activation_checks
    
    echo ""
    success "Phase 7 activation completed!"
    echo ""
    log "Next: Phase 8 will auto-execute after validation"
    log "To trigger Phase 8: bash $BASE_PATH/tools/auto_execute_plan_v24.sh"
    echo ""
}

# Execute
main "$@"
