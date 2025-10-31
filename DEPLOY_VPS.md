# 🚀 Guide Déploiement VPS - SmartOrder PRO
**by MAIGA ABOUBACAR**

## 📋 Prérequis

- VPS Ubuntu 20.04+ (4GB RAM minimum)
- IP: `107.189.22.255`
- Port Web: `8555`
- Accès SSH root

## 🔧 Installation Rapide

### 1. Connexion SSH
```bash
ssh root@107.189.22.255
```

### 2. Installation Dépendances
```bash
apt update && apt upgrade -y
apt install python3.9 python3-pip git nginx supervisor -y
```

### 3. Clone Projet
```bash
cd /opt
git clone https://github.com/votre-repo/smartorder-pro-ai-v1.7.git
cd smartorder-pro-ai-v1.7
```

### 4. Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configuration .env
```bash
cp .env.example .env
nano .env
```

Configurer:
```env
# TRADING
PAPER_TRADING=false
ACTIVE_EXCHANGE=bybit

# BYBIT
BYBIT_API_KEY=votre_api_key
BYBIT_API_SECRET=votre_api_secret

# TELEGRAM
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id

# DASHBOARD
DASHBOARD_PORT=8555
DASHBOARD_HOST=0.0.0.0
```

### 6. Supervisor (Auto-démarrage)
```bash
nano /etc/supervisor/conf.d/smartorder.conf
```

Contenu:
```ini
[program:smartorder]
command=/opt/smartorder-pro-ai-v1.7/venv/bin/python main.py
directory=/opt/smartorder-pro-ai-v1.7
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/smartorder.log

[program:smartorder-web]
command=/opt/smartorder-pro-ai-v1.7/venv/bin/python -m http.server 8555 --directory /opt/smartorder-pro-ai-v1.7/web
directory=/opt/smartorder-pro-ai-v1.7
user=root
autostart=true
autorestart=true
```

Activer:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start smartorder smartorder-web
```

### 7. Nginx (Reverse Proxy)
```bash
nano /etc/nginx/sites-available/smartorder
```

Contenu:
```nginx
server {
    listen 80;
    server_name 107.189.22.255;

    location / {
        proxy_pass http://127.0.0.1:8555;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Activer:
```bash
ln -s /etc/nginx/sites-available/smartorder /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 8. Firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 8555/tcp
ufw enable
```

## 🎯 Vérification

```bash
# Vérifier services
supervisorctl status

# Logs
tail -f /var/log/smartorder.log

# Test web
curl http://107.189.22.255:8555
```

## 📱 Accès Dashboard

```
http://107.189.22.255:8555/unified_dashboard.html
```

## 🤖 Démarrer Bot Telegram

```bash
cd /opt/smartorder-pro-ai-v1.7
source venv/bin/activate
python telegram/advanced_bot.py
```

## ⚙️ Commandes Utiles

```bash
# Redémarrer bot
supervisorctl restart smartorder

# Voir logs
tail -f /var/log/smartorder.log

# Mettre à jour
cd /opt/smartorder-pro-ai-v1.7
git pull
supervisorctl restart smartorder

# Backup config
cp config/*.json /backup/
```

## 🔐 Sécurité

1. **IP Whitelist** sur exchanges
2. **2FA** activé
3. **SSH Key Only**:
```bash
nano /etc/ssh/sshd_config
# PasswordAuthentication no
systemctl restart sshd
```

## 🛠️ Troubleshooting

### Bot ne démarre pas
```bash
supervisorctl tail smartorder
python main.py  # Test manuel
```

### Dashboard inaccessible
```bash
netstat -tulpn | grep 8555
supervisorctl restart smartorder-web
```

### Erreur API Exchange
```bash
# Vérifier .env
cat .env | grep API_KEY
# Test connexion
python -c "from core.bybit_client import test_connection; test_connection()"
```

## ✅ Checklist Déploiement

- [ ] VPS configuré (Ubuntu 20.04+)
- [ ] Python 3.9+ installé
- [ ] Projet cloné dans /opt
- [ ] .env configuré avec vraies API keys
- [ ] Supervisor configuré et actif
- [ ] Nginx reverse proxy actif
- [ ] Firewall configuré
- [ ] Dashboard accessible
- [ ] Bot Telegram répond
- [ ] Logs sans erreur
- [ ] IP whitelistée sur exchanges

## 📊 Monitoring

```bash
# CPU/RAM
htop

# Espace disque
df -h

# Logs temps réel
tail -f /var/log/smartorder.log

# Status services
systemctl status nginx supervisor
```

## 🔄 Mise à Jour

```bash
cd /opt/smartorder-pro-ai-v1.7
git pull
source venv/bin/activate
pip install -r requirements.txt
supervisorctl restart smartorder
```

---

**✅ DÉPLOIEMENT TERMINÉ !**
Dashboard: http://107.189.22.255:8555/unified_dashboard.html
