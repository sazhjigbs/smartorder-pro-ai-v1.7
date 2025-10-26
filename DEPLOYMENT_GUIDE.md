# 🚀 GUIDE DE DÉPLOIEMENT - SmartOrder PRO

**Version :** v1.8-FINAL  
**Date :** 26 Octobre 2025

---

## 📋 PRÉREQUIS AVANT DÉPLOIEMENT

### ✅ Checklist Locale
- [x] Auto-backup configuré (`scripts/auto_backup.sh`)
- [x] Logger structuré (`core/logger.py`)
- [x] Tests unitaires (`tests/test_router.py`)
- [ ] Tests passent: `pytest tests/ -v`
- [ ] Git commit & push final
- [ ] Variables `.env` configurées

### ⚙️ VPS Requis
- **OS :** Ubuntu 20.04+ ou Debian 11+
- **RAM :** 2 GB minimum (4 GB recommandé)
- **CPU :** 2 cores minimum
- **Disk :** 20 GB minimum
- **Python :** 3.9+

---

## 🔧 ÉTAPE 1 : PRÉPARATION VPS

### 1.1 Connexion SSH
```bash
ssh root@107.189.22.255
```

### 1.2 Mise à jour système
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git htop curl wget
```

### 1.3 Créer utilisateur (sécurité)
```bash
adduser smartorder
usermod -aG sudo smartorder
su - smartorder
```

### 1.4 Installer packages système
```bash
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    supervisor \
    nginx
```

---

## 📦 ÉTAPE 2 : DÉPLOIEMENT CODE

### 2.1 Cloner repository
```bash
cd /opt
sudo mkdir smartorder-pro
sudo chown smartorder:smartorder smartorder-pro
cd smartorder-pro

git clone https://github.com/sazhjigbs/smartorder-pro-ai-v1.7.git .
```

### 2.2 Créer environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Installer dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Pour tests
```

### 2.4 Vérifier installation
```bash
python3 -c "import fastapi, ccxt, requests; print('✅ OK')"
```

---

## 🔐 ÉTAPE 3 : CONFIGURATION

### 3.1 Copier fichier .env
```bash
cp .env.example .env
nano .env
```

**Variables critiques à configurer :**
```bash
# Exchanges
BYBIT_API_KEY=your_key_here
BYBIT_API_SECRET=your_secret_here
BINANCE_API_KEY=optional
BINANCE_API_SECRET=optional

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id

# Mode
REAL_MODE=false  # false = simulation, true = LIVE
AUTO_MODE=true
ACTIVE_EXCHANGE=bybit

# Sécurité
ADMIN_TOKEN=your_secure_token_here

# Trading
MAX_LEVERAGE=20
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
```

### 3.2 Créer dossiers nécessaires
```bash
mkdir -p logs backups db
chmod 755 logs backups db
```

### 3.3 Configuration backup automatique
```bash
chmod +x scripts/auto_backup.sh

# Ajouter au crontab
crontab -e

# Ajouter cette ligne:
0 */6 * * * /opt/smartorder-pro/venv/bin/python /opt/smartorder-pro/scripts/auto_backup.sh >> /opt/smartorder-pro/logs/cron.log 2>&1
```

---

## 🔄 ÉTAPE 4 : SYSTEMD SERVICES

### 4.1 Service Portal Web
```bash
sudo nano /etc/systemd/system/smartorder-portal.service
```

```ini
[Unit]
Description=SmartOrder PRO Portal Web
After=network.target

[Service]
Type=simple
User=smartorder
WorkingDirectory=/opt/smartorder-pro
Environment="PATH=/opt/smartorder-pro/venv/bin"
ExecStart=/opt/smartorder-pro/venv/bin/python web/portal_v5_pro/main_unified.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.2 Service Execution Bridge
```bash
sudo nano /etc/systemd/system/smartorder-executor.service
```

```ini
[Unit]
Description=SmartOrder PRO Execution Bridge
After=network.target smartorder-portal.service

[Service]
Type=simple
User=smartorder
WorkingDirectory=/opt/smartorder-pro
Environment="PATH=/opt/smartorder-pro/venv/bin"
ExecStart=/opt/smartorder-pro/venv/bin/python executor/execution_bridge_clean.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.3 Service Self-Learning Loop
```bash
sudo nano /etc/systemd/system/smartorder-learning.service
```

```ini
[Unit]
Description=SmartOrder PRO Self-Learning AI
After=network.target

[Service]
Type=simple
User=smartorder
WorkingDirectory=/opt/smartorder-pro
Environment="PATH=/opt/smartorder-pro/venv/bin"
ExecStart=/opt/smartorder-pro/venv/bin/python ai_core/self_learning_loop.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.4 Service Guardian
```bash
sudo nano /etc/systemd/system/smartorder-guardian.service
```

```ini
[Unit]
Description=SmartOrder PRO Guardian AI
After=network.target

[Service]
Type=simple
User=smartorder
WorkingDirectory=/opt/smartorder-pro
Environment="PATH=/opt/smartorder-pro/venv/bin"
ExecStart=/opt/smartorder-pro/venv/bin/python tools/guardian_notify.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.5 Activer et démarrer services
```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer au démarrage
sudo systemctl enable smartorder-portal
sudo systemctl enable smartorder-executor
sudo systemctl enable smartorder-learning
sudo systemctl enable smartorder-guardian

# Démarrer services
sudo systemctl start smartorder-portal
sudo systemctl start smartorder-executor
sudo systemctl start smartorder-learning
sudo systemctl start smartorder-guardian

# Vérifier statut
sudo systemctl status smartorder-portal
sudo systemctl status smartorder-executor
```

---

## 🧪 ÉTAPE 5 : TESTS

### 5.1 Tests unitaires
```bash
cd /opt/smartorder-pro
source venv/bin/activate
pytest tests/ -v
```

### 5.2 Test API Health
```bash
curl http://localhost:8555/api/system_status
curl http://localhost:8555/api/live_status
```

**Réponse attendue :**
```json
{
  "status": "ok",
  "version": "v1.8-FINAL",
  "services": {
    "portal": "running",
    "executor": "running"
  }
}
```

### 5.3 Test Router
```bash
python3 -c "from core.router import choose_exchange; print(choose_exchange('BTCUSDT', 0.001, 67000))"
```

### 5.4 Test Paper Trading
```bash
# Vérifier que REAL_MODE=false dans .env
grep REAL_MODE .env

# Tester ordre simulation
python3 test_order_simulation.py
```

---

## 📊 ÉTAPE 6 : MONITORING

### 6.1 Logs en temps réel
```bash
# Logs portal
sudo journalctl -u smartorder-portal -f

# Logs executor
sudo journalctl -u smartorder-executor -f

# Logs JSON structurés
tail -f logs/execution.json | jq .
```

### 6.2 Ressources système
```bash
htop

# CPU/RAM usage
free -h
df -h
```

### 6.3 Status services
```bash
# Script rapide
cat > check_services.sh << 'EOF'
#!/bin/bash
echo "=== SmartOrder Services Status ==="
for svc in smartorder-portal smartorder-executor smartorder-learning smartorder-guardian; do
    status=$(systemctl is-active $svc)
    if [ "$status" = "active" ]; then
        echo "✅ $svc: $status"
    else
        echo "❌ $svc: $status"
    fi
done
EOF

chmod +x check_services.sh
./check_services.sh
```

---

## 🔒 ÉTAPE 7 : SÉCURITÉ

### 7.1 Firewall (UFW)
```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8555/tcp  # Portal (si accès externe nécessaire)
sudo ufw enable
```

### 7.2 Fail2Ban (protection SSH)
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 7.3 SSL/TLS (si domaine)
```bash
# Avec Certbot + Nginx
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 7.4 Permissions fichiers
```bash
chmod 600 .env
chmod 700 backups/
chmod 644 logs/*.log
```

---

## 🎯 ÉTAPE 8 : PASSAGE EN LIVE

⚠️ **ATTENTION : Vérifier 3 fois avant de passer en LIVE**

### 8.1 Checklist pré-LIVE
- [ ] Tests simulation réussis (24h minimum)
- [ ] Backup automatique fonctionne
- [ ] Logs structurés actifs
- [ ] Notifications Telegram fonctionnent
- [ ] Capital de test uniquement (10-50 USDT)
- [ ] Stop-loss configurés
- [ ] Guardian AI actif

### 8.2 Activer mode LIVE
```bash
# Modifier .env
nano .env

# Changer:
REAL_MODE=true

# Redémarrer services
sudo systemctl restart smartorder-executor
```

### 8.3 Monitoring intensif (première heure)
```bash
# Ouvrir 4 terminaux:

# Terminal 1: Logs executor
sudo journalctl -u smartorder-executor -f

# Terminal 2: Logs portal
sudo journalctl -u smartorder-portal -f

# Terminal 3: Logs JSON
tail -f logs/execution.json | jq .

# Terminal 4: Ressources
watch -n 5 'free -h && df -h'
```

---

## 🚨 DÉPANNAGE

### Problème : Service ne démarre pas
```bash
# Voir logs erreur
sudo journalctl -u smartorder-portal -n 50 --no-pager

# Vérifier config
python3 -m py_compile web/portal_v5_pro/main_unified.py

# Permissions
sudo chown -R smartorder:smartorder /opt/smartorder-pro
```

### Problème : Erreur API exchange
```bash
# Tester connexion Bybit
python3 -c "from core.bybit_client import BybitClient; client = BybitClient(); print(client.get_balance())"

# Vérifier clés API
grep BYBIT_API .env
```

### Problème : RAM saturée
```bash
# Identifier processus gourmands
ps aux --sort=-%mem | head -10

# Redémarrer service lourd
sudo systemctl restart smartorder-learning
```

### Problème : Logs trop volumineux
```bash
# Nettoyer vieux logs
find logs/ -name "*.log" -mtime +7 -delete
find logs/ -name "*.json" -mtime +7 -delete

# Configurer logrotate
sudo nano /etc/logrotate.d/smartorder
```

---

## 📞 COMMANDES UTILES

```bash
# Status complet
./scripts/check_full_status.sh

# Redémarrer tout
sudo systemctl restart smartorder-*

# Arrêter tout
sudo systemctl stop smartorder-*

# Backup manuel
./scripts/auto_backup.sh

# Update code depuis Git
cd /opt/smartorder-pro
git pull origin main
sudo systemctl restart smartorder-*

# Voir version
cat VERSION
```

---

## ✅ DÉPLOIEMENT TERMINÉ

Ton bot SmartOrder PRO est maintenant en production ! 🎉

**Prochaines étapes :**
1. Surveiller logs pendant 24-48h en mode simulation
2. Tester tous les scénarios (ordres, stop-loss, etc.)
3. Passer en LIVE avec capital minimal
4. Ajouter progressivement les fonctionnalités avancées

**Support :** Voir `ANALYSE_FINALE_AVANT_DEPLOIEMENT.md` pour roadmap complète

---

**Document créé le :** 26 Octobre 2025  
**Version bot :** v1.8-FINAL
