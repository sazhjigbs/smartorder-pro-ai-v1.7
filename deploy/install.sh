#!/bin/bash
# 🚀 SAFELOGIC SmartOrder PRO — Installation VPS complète
# Bismillah ! Optimisé pour VPS faible RAM

echo "🚀 SmartOrder PRO - Installation VPS"
echo "======================================"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Config
PROJECT_DIR="/opt/smartorder-pro"
BACKUP_DIR="/opt/smartorder-backups"
VENV_DIR="$PROJECT_DIR/venv"

# 1. Backup avant tout
echo -e "${YELLOW}📦 Creating safety backup...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    tar -czf "/tmp/smartorder_pre_install_$(date +%Y%m%d_%H%M%S).tar.gz" \
        -C /opt smartorder-pro \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='venv' 2>/dev/null
    echo -e "${GREEN}✅ Backup created${NC}"
fi

# 2. Git pull latest
echo -e "${YELLOW}🔄 Pulling latest from GitHub...${NC}"
cd $PROJECT_DIR
git stash 2>/dev/null
git pull origin main
echo -e "${GREEN}✅ Code updated${NC}"

# 3. Install Python deps (léger)
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip3 install --no-cache-dir -q \
    requests \
    psutil \
    schedule \
    python-dotenv \
    2>/dev/null
echo -e "${GREEN}✅ Dependencies installed${NC}"

# 4. Setup directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p $BACKUP_DIR
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/db
chmod 755 $PROJECT_DIR/tools/*.py 2>/dev/null
echo -e "${GREEN}✅ Directories ready${NC}"

# 5. Install systemd services
echo -e "${YELLOW}⚙️ Installing systemd services...${NC}"

# Service backup
if [ -f "$PROJECT_DIR/deploy/smartorder-backup.service" ]; then
    cp $PROJECT_DIR/deploy/smartorder-backup.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable smartorder-backup.service
    echo -e "${GREEN}✅ Backup service installed${NC}"
fi

# 6. Restart services
echo -e "${YELLOW}🔄 Restarting services...${NC}"
systemctl restart smartorder-backup 2>/dev/null
systemctl restart smartorder-portal 2>/dev/null
systemctl restart smartorder-bridge 2>/dev/null

# Wait services
sleep 3

# 7. Status check
echo ""
echo -e "${GREEN}📊 Services Status:${NC}"
echo "==================="

for service in smartorder-backup smartorder-portal smartorder-bridge; do
    if systemctl is-active --quiet $service; then
        echo -e "  ${GREEN}✅ $service - Running${NC}"
    else
        echo -e "  ${RED}❌ $service - Stopped${NC}"
    fi
done

# 8. Health check
echo ""
echo -e "${GREEN}🏥 System Health:${NC}"
echo "=================="
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
DISK=$(df -h /opt | tail -1 | awk '{print $5}' | tr -d '%')

echo "  CPU: ${CPU}%"
echo "  RAM: ${MEM}%"
echo "  Disk: ${DISK}%"

# 9. Test backup
echo ""
echo -e "${YELLOW}🧪 Testing backup system...${NC}"
python3 $PROJECT_DIR/tools/auto_backup.py --once 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup test OK${NC}"
else
    echo -e "${RED}⚠️ Backup test failed (non-critical)${NC}"
fi

# 10. Final
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "📝 Next steps:"
echo "  1. Check logs: journalctl -u smartorder-portal -f"
echo "  2. Monitor: systemctl status smartorder-*"
echo "  3. Backups: ls -lh $BACKUP_DIR"
echo ""
echo "🚀 SmartOrder PRO is ready!"
