#!/bin/bash
# 🚀 SAFELOGIC Auto-Deploy Script - VPS Integration
# Auto-sync GitHub → VPS avec restart intelligent

echo "🔄 SAFELOGIC AUTO-DEPLOY STARTING..."
echo "======================================="

# Configuration
VPS_DIR="/opt/smartorder-pro"
BACKUP_DIR="/opt/backups"
LOG_FILE="/opt/smartorder-pro/logs/auto_deploy.log"

# Function pour logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Sauvegarde avant mise à jour
create_backup() {
    log_message "🛡️ Creating backup..."
    mkdir -p "$BACKUP_DIR"
    cd "$VPS_DIR"
    
    backup_name="smartorder_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$BACKUP_DIR/$backup_name" . --exclude='venv' --exclude='.git' --exclude='logs/*.log'
    
    log_message "✅ Backup created: $backup_name"
    
    # Garder seulement les 5 dernières sauvegardes
    cd "$BACKUP_DIR"
    ls -t smartorder_backup_*.tar.gz | tail -n +6 | xargs -r rm
}

# Pull depuis GitHub
github_pull() {
    log_message "📥 Pulling from GitHub..."
    cd "$VPS_DIR"
    
    # Stash local changes (logs)
    git stash push -u -m "Auto-stash before deployment $(date)"
    
    # Pull latest changes
    if git pull origin main; then
        log_message "✅ GitHub pull successful"
        return 0
    else
        log_message "❌ GitHub pull failed"
        return 1
    fi
}

# Détection des changements critiques
detect_critical_changes() {
    log_message "🔍 Detecting critical changes..."
    
    # Check si changements dans les services principaux
    if git diff HEAD~1 HEAD --name-only | grep -E "(core/|ai_core/|web/portal_v5_pro/|main.py)"; then
        log_message "🚨 Critical changes detected - Full restart needed"
        echo "FULL_RESTART"
    else
        log_message "ℹ️ Minor changes - Selective restart"
        echo "SELECTIVE_RESTART"
    fi
}

# Restart services intelligents
restart_services() {
    local restart_type="$1"
    log_message "🔄 Restarting services ($restart_type)..."
    
    if [ "$restart_type" = "FULL_RESTART" ]; then
        # Restart critique
        systemctl restart smartorder-portal-v5
        systemctl restart smartorder-pro
        systemctl restart smartorder-websync-bridge
        systemctl restart smartorder-dashboard-v4
        
        log_message "🚀 Full services restart completed"
    else
        # Restart sélectif (seulement si nécessaire)
        systemctl reload smartorder-portal-v5 2>/dev/null || systemctl restart smartorder-portal-v5
        log_message "🔄 Selective restart completed"
    fi
}

# Vérification santé post-déploiement
health_check() {
    log_message "🏥 Running health checks..."
    
    # Check ports actifs
    for port in 8555 8191 8181; do
        if ss -tulnp | grep ":$port" > /dev/null; then
            log_message "✅ Port $port active"
        else
            log_message "❌ Port $port inactive - Issue detected"
            return 1
        fi
    done
    
    # Check services critiques
    for service in smartorder-portal-v5 smartorder-pro smartorder-websync-bridge; do
        if systemctl is-active "$service" > /dev/null; then
            log_message "✅ Service $service active"
        else
            log_message "❌ Service $service inactive"
            return 1
        fi
    done
    
    log_message "🎉 All health checks passed!"
    return 0
}

# Notification Telegram (si configuré)
send_notification() {
    local message="$1"
    local emoji="$2"
    
    if [ -f "$VPS_DIR/.env" ] && grep -q "TG_TOKEN" "$VPS_DIR/.env"; then
        # Extract Telegram config from .env
        source "$VPS_DIR/.env"
        
        if [ ! -z "$TG_TOKEN" ] && [ ! -z "$TG_CHAT_ID" ]; then
            curl -s -X POST "https://api.telegram.org/bot$TG_TOKEN/sendMessage" \
                -d chat_id="$TG_CHAT_ID" \
                -d text="$emoji SAFELOGIC AUTO-DEPLOY: $message" \
                -d parse_mode="Markdown" > /dev/null
            
            log_message "📱 Telegram notification sent"
        fi
    fi
}

# MAIN EXECUTION
main() {
    log_message "🚀 Auto-deployment initiated"
    send_notification "Deployment started" "🔄"
    
    # 1. Backup
    create_backup
    
    # 2. Pull from GitHub
    if ! github_pull; then
        log_message "💥 Deployment failed at GitHub pull"
        send_notification "Deployment FAILED at GitHub pull" "❌"
        exit 1
    fi
    
    # 3. Detect changes
    restart_type=$(detect_critical_changes)
    
    # 4. Restart services
    restart_services "$restart_type"
    
    # 5. Health check
    sleep 10  # Wait for services to stabilize
    
    if health_check; then
        log_message "🎉 Deployment completed successfully!"
        send_notification "Deployment SUCCESSFUL - All systems operational" "✅"
    else
        log_message "💥 Deployment completed but health check failed"
        send_notification "Deployment completed but HEALTH CHECK FAILED" "⚠️"
        exit 1
    fi
    
    # 6. Cleanup
    git stash clear  # Clear auto-stash
    
    log_message "🏁 Auto-deployment finished"
}

# Execute main function
main "$@"