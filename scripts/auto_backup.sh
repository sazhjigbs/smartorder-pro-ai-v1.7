#!/bin/bash

# ==============================================================================
# AUTO BACKUP SMARTORDER PRO
# ==============================================================================
# Description: Sauvegarde automatique du bot avec compression et rotation
# Usage: ./auto_backup.sh
# Cron: 0 */6 * * * /opt/smartorder-pro/scripts/auto_backup.sh
# ==============================================================================

set -e  # Exit on error

# Configuration
BACKUP_DIR="/opt/smartorder-backups"
PROJECT_DIR="/opt/smartorder-pro"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_smartorder_${DATE}.tar.gz"
LOG_FILE="/opt/smartorder-pro/logs/backup.log"
MAX_BACKUPS=28  # Garde 28 backups (7 jours * 4 backups/jour)

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Créer le répertoire de backup si nécessaire
if [ ! -d "$BACKUP_DIR" ]; then
    log "Création du répertoire de backup: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Vérifier l'espace disque disponible
AVAILABLE_SPACE=$(df -BG "$BACKUP_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 2 ]; then
    error "Espace disque insuffisant: ${AVAILABLE_SPACE}G disponible"
    exit 1
fi

log "=========================================="
log "Démarrage backup automatique"
log "Destination: $BACKUP_DIR/$BACKUP_FILE"
log "=========================================="

# Créer le backup
log "Compression en cours..."
cd "$PROJECT_DIR" || exit 1

# Exclure certains dossiers lourds
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='logs/*.log' \
    --exclude='*.tar.gz' \
    . 2>/dev/null || {
        error "Échec de la compression"
        exit 1
    }

# Vérifier la taille du backup
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
log "✅ Backup créé: $BACKUP_FILE ($BACKUP_SIZE)"

# Rotation des anciens backups (garde les MAX_BACKUPS plus récents)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_smartorder_*.tar.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    log "Rotation: suppression des anciens backups (garde les $MAX_BACKUPS plus récents)"
    ls -1t "$BACKUP_DIR"/backup_smartorder_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
    log "✅ Rotation effectuée"
fi

# Statistiques finales
TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/backup_smartorder_*.tar.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "=========================================="
log "📊 Statistiques:"
log "   - Backups totaux: $TOTAL_BACKUPS"
log "   - Espace utilisé: $TOTAL_SIZE"
log "   - Dernier backup: $BACKUP_FILE ($BACKUP_SIZE)"
log "=========================================="
log "✅ Backup automatique terminé avec succès"

# Envoyer notification (optionnel - si telegram bot configuré)
if [ -f "$PROJECT_DIR/tools/guardian_notify.py" ]; then
    python3 "$PROJECT_DIR/tools/guardian_notify.py" \
        "🔒 Backup auto créé\n📦 $BACKUP_FILE ($BACKUP_SIZE)\n📊 Total: $TOTAL_BACKUPS backups" \
        2>/dev/null || warning "Notification Telegram échouée"
fi

exit 0
