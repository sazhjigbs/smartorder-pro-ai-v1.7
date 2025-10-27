# VPS DEPLOYMENT GUIDE
## SmartOrder PRO v1.9-FINAL
**by MAIGA ABOUBACAR**

---

## 1. REQUIREMENTS VPS

### Specifications Minimales
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04+ LTS
- **Network**: 100Mbps

### Recommended Providers
- DigitalOcean (Droplet $20/month)
- Vultr (Cloud Compute $18/month)
- Linode (Shared CPU $20/month)
- AWS EC2 (t3.medium)

---

## 2. INITIAL SETUP

### Connect to VPS
```bash
ssh root@YOUR_VPS_IP
```

### Update System
```bash
apt update && apt upgrade -y
```

### Install Dependencies
```bash
# Python 3.9+
apt install python3 python3-pip python3-venv -y

# Git
apt install git -y

# Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Create User
```bash
adduser smartorder
usermod -aG sudo smartorder
su - smartorder
```

---

## 3. DEPLOY APPLICATION

### Clone Repository
```bash
cd /home/smartorder
git clone <YOUR_REPO_URL> smartorder-pro
cd smartorder-pro
```

### Setup Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure .env
```bash
cp .env.example .env
nano .env
```

**Critical variables**:
```env
PAPER_TRADING=false  # REAL TRADING!
USE_TESTNET=false    # REAL MONEY!

# Add your real API keys
BYBIT_API_KEY=xxx
BYBIT_API_SECRET=xxx
# ... (other exchanges)

# Security
ENCRYPTION_MASTER_KEY=xxx
```

### Setup Encryption
```bash
python3 security/database_encryption.py setup
# Save the generated key!

# Store API keys
python3 security/database_encryption.py store
```

---

## 4. FIREWALL CONFIGURATION

```bash
# Enable firewall
ufw enable

# Allow SSH
ufw allow 22/tcp

# Allow dashboard (change if using domain)
ufw allow 8555/tcp

# Allow HTTPS (if using SSL)
ufw allow 443/tcp

# Check status
ufw status
```

---

## 5. START APPLICATION

### Option A: Direct Start
```bash
# Make executable
chmod +x startup_production.sh shutdown.sh

# Start
./startup_production.sh

# Check logs
tail -f logs/dashboard.log
```

### Option B: Docker
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker logs -f smartorder-pro

# Stop
docker-compose -f docker-compose.prod.yml down
```

### Option C: Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/smartorder.service
```

Content:
```ini
[Unit]
Description=SmartOrder PRO Trading Bot
After=network.target

[Service]
Type=simple
User=smartorder
WorkingDirectory=/home/smartorder/smartorder-pro
Environment="PATH=/home/smartorder/smartorder-pro/venv/bin"
ExecStart=/home/smartorder/smartorder-pro/venv/bin/python3 dashboard/main_unified.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartorder
sudo systemctl start smartorder
sudo systemctl status smartorder
```

---

## 6. DOMAIN & SSL (Optional)

### Point Domain to VPS
Add A record: `bot.yourdomain.com` → `YOUR_VPS_IP`

### Install Nginx
```bash
sudo apt install nginx -y
```

### Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/smartorder
```

Content:
```nginx
server {
    listen 80;
    server_name bot.yourdomain.com;

    location / {
        proxy_pass http://localhost:8555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/smartorder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Install SSL (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d bot.yourdomain.com
```

---

## 7. MONITORING

### Check Health
```bash
curl http://localhost:8555/health
```

### View Logs
```bash
tail -f logs/all.log
tail -f logs/error.log
```

### Check Process
```bash
ps aux | grep python
```

### System Resources
```bash
htop
df -h
free -m
```

---

## 8. BACKUP SETUP

### Create Backup Script
```bash
nano backup.sh
```

Content:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/smartorder/backups"
mkdir -p $BACKUP_DIR

# Backup database
cp data/smartorder.db $BACKUP_DIR/smartorder_$DATE.db

# Backup logs (last 7 days)
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Keep only last 7 backups
ls -t $BACKUP_DIR/*.db | tail -n +8 | xargs rm -f
ls -t $BACKUP_DIR/*.tar.gz | tail -n +8 | xargs rm -f

echo "Backup completed: $DATE"
```

### Schedule with Cron
```bash
chmod +x backup.sh
crontab -e
```

Add:
```cron
# Backup every day at 3 AM
0 3 * * * /home/smartorder/smartorder-pro/backup.sh
```

---

## 9. MAINTENANCE

### Update Code
```bash
cd /home/smartorder/smartorder-pro
git pull
pip install -r requirements.txt
sudo systemctl restart smartorder
```

### Rotate Logs
Logs auto-rotate at 10MB (built-in)

### Check Disk Space
```bash
df -h
# If >80%, clean old logs:
find logs/ -name "*.log.*" -mtime +7 -delete
```

---

## 10. TROUBLESHOOTING

### Bot Not Starting
```bash
# Check logs
cat logs/dashboard.log

# Check Python errors
python3 dashboard/main_unified.py

# Check permissions
ls -la
```

### API Errors
```bash
# Test exchanges
python3 tests/test_multi_exchange.py

# Check API keys
python3 -c "import os; print(os.getenv('BYBIT_API_KEY'))"
```

### High CPU/Memory
```bash
# Check processes
top
htop

# Restart service
sudo systemctl restart smartorder
```

---

## 11. SECURITY CHECKLIST

- [ ] SSH key authentication (disable password login)
- [ ] Firewall enabled and configured
- [ ] API keys encrypted in database
- [ ] No Withdraw permission on exchange APIs
- [ ] IP whitelist on exchange APIs
- [ ] SSL certificate installed (if using domain)
- [ ] Regular backups scheduled
- [ ] Monitoring/alerts configured
- [ ] Strong passwords everywhere
- [ ] `.env` file has correct permissions (600)

```bash
chmod 600 .env
```

---

## 12. SUPPORT

**Issues**: Check logs first  
**Updates**: `git pull && pip install -r requirements.txt`  
**Emergency Stop**: `./shutdown.sh` or `sudo systemctl stop smartorder`

---

**DEPLOYMENT COMPLETE!** 🚀

Bot accessible at: http://YOUR_VPS_IP:8555 or https://bot.yourdomain.com

---

by MAIGA ABOUBACAR  
SmartOrder PRO v1.9-FINAL
