# 🚀 GUIDE DÉPLOIEMENT RÉEL - SMARTORDER PRO

**Version:** v1.8-FINAL  
**Date:** 2025-01-26  
**Complétion:** 98%

---

## 📋 TABLE DES MATIÈRES

1. [Test Local (Windows)](#test-local-windows)
2. [Déploiement VPS Production](#deploiement-vps-production)
3. [Configuration Bybit](#configuration-bybit)
4. [Lancement des Services](#lancement-services)
5. [Vérification](#verification)
6. [Troubleshooting](#troubleshooting)

---

# 🖥️ TEST LOCAL (WINDOWS)

## Prérequis

- ✅ Python 3.8+ installé
- ✅ Git installé
- ✅ Compte Bybit avec API Keys
- ✅ Bot Telegram créé (optionnel)

## Étape 1: Vérifier Python

```powershell
python --version
# Ou
python3 --version
```

**Si Python n'est pas installé:**
1. Télécharger: https://www.python.org/downloads/
2. Cocher "Add Python to PATH" pendant l'installation
3. Redémarrer le terminal

## Étape 2: Installer les dépendances

```powershell
cd C:\Users\aimet\smartorder-pro-ai-v1.7

# Installer les packages
pip install -r requirements.txt

# Ou manuellement:
pip install fastapi uvicorn python-telegram-bot requests pybit websockets
```

## Étape 3: Configuration Bybit

Créer fichier `.env` à la racine:

```env
# Bybit API
BYBIT_API_KEY=votre_api_key
BYBIT_API_SECRET=votre_api_secret
BYBIT_TESTNET=false

# Telegram (optionnel)
TELEGRAM_BOT_TOKEN=votre_bot_token
TELEGRAM_CHAT_ID=votre_chat_id
```

**⚠️ IMPORTANT:** Ne jamais commit le fichier `.env` !

## Étape 4: Lancer les APIs

### Terminal 1: API Sentiment
```powershell
python api/api_sentiment.py
```
→ API sur http://localhost:8558

### Terminal 2: API Mode Manager
```powershell
python api/api_mode.py
```
→ API sur http://localhost:8560

### Terminal 3: API PnL Live (optionnel)
```powershell
python api/api_pnl_live.py
```
→ API sur http://localhost:8556

### Terminal 4: API Signal Memory (optionnel)
```powershell
python api/api_signal_memory.py
```
→ API sur http://localhost:8557

### Terminal 5: API Smart Execution (optionnel)
```powershell
python api/api_execution_smart.py
```
→ API sur http://localhost:8559

## Étape 5: Ouvrir l'Interface Web

1. Ouvrir `web/mode_switcher.html` dans un navigateur
2. Vérifier que les APIs sont accessibles
3. Tester les boutons de changement de mode

## Étape 6: Lancer Bot Telegram (optionnel)

```powershell
# Éditer telegram/mode_handler.py
# Ligne 485: Remplacer "YOUR_TELEGRAM_BOT_TOKEN" par votre token

python telegram/mode_handler.py
```

---

# 🌐 DÉPLOIEMENT VPS PRODUCTION

## Prérequis VPS

- Ubuntu 20.04+ ou Debian 11+
- 2GB RAM minimum
- 20GB disque
- Python 3.8+
- Accès SSH

## Étape 1: Connexion SSH

```bash
ssh root@votre_ip_vps
```

## Étape 2: Mise à jour système

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip git nginx supervisor
```

## Étape 3: Cloner le projet

```bash
cd /opt
git clone https://github.com/sazhjigbs/smartorder-pro-ai-v1.7.git
cd smartorder-pro-ai-v1.7
```

## Étape 4: Installer dépendances

```bash
pip3 install -r requirements.txt
```

## Étape 5: Configuration

```bash
nano .env
```

Ajouter:
```env
BYBIT_API_KEY=votre_api_key
BYBIT_API_SECRET=votre_api_secret
BYBIT_TESTNET=false
TELEGRAM_BOT_TOKEN=votre_bot_token
TELEGRAM_CHAT_ID=votre_chat_id
```

Sauvegarder: `Ctrl+X`, `Y`, `Enter`

## Étape 6: Supervisor (auto-restart)

### Créer config pour API Sentiment

```bash
nano /etc/supervisor/conf.d/smartorder-sentiment.conf
```

Contenu:
```ini
[program:smartorder-sentiment]
command=/usr/bin/python3 /opt/smartorder-pro-ai-v1.7/api/api_sentiment.py
directory=/opt/smartorder-pro-ai-v1.7
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/smartorder-sentiment.err.log
stdout_logfile=/var/log/smartorder-sentiment.out.log
```

### Créer config pour API Mode

```bash
nano /etc/supervisor/conf.d/smartorder-mode.conf
```

Contenu:
```ini
[program:smartorder-mode]
command=/usr/bin/python3 /opt/smartorder-pro-ai-v1.7/api/api_mode.py
directory=/opt/smartorder-pro-ai-v1.7
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/smartorder-mode.err.log
stdout_logfile=/var/log/smartorder-mode.out.log
```

### Créer config pour Bot Telegram

```bash
nano /etc/supervisor/conf.d/smartorder-telegram.conf
```

Contenu:
```ini
[program:smartorder-telegram]
command=/usr/bin/python3 /opt/smartorder-pro-ai-v1.7/telegram/mode_handler.py
directory=/opt/smartorder-pro-ai-v1.7
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/smartorder-telegram.err.log
stdout_logfile=/var/log/smartorder-telegram.out.log
```

### Recharger Supervisor

```bash
supervisorctl reread
supervisorctl update
supervisorctl start all
```

### Vérifier status

```bash
supervisorctl status
```

Résultat attendu:
```
smartorder-mode      RUNNING   pid 1234, uptime 0:00:05
smartorder-sentiment RUNNING   pid 1235, uptime 0:00:05
smartorder-telegram  RUNNING   pid 1236, uptime 0:00:05
```

## Étape 7: Nginx (reverse proxy)

```bash
nano /etc/nginx/sites-available/smartorder
```

Contenu:
```nginx
server {
    listen 80;
    server_name votre_domaine.com;  # ou IP du VPS

    # Interface Web
    location / {
        root /opt/smartorder-pro-ai-v1.7/web;
        index mode_switcher.html;
        try_files $uri $uri/ =404;
    }

    # API Sentiment
    location /api/sentiment {
        proxy_pass http://localhost:8558;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API Mode
    location /api/mode {
        proxy_pass http://localhost:8560;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API PnL
    location /api/pnl {
        proxy_pass http://localhost:8556;
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
systemctl reload nginx
```

## Étape 8: SSL (HTTPS) - Optionnel mais recommandé

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d votre_domaine.com
```

---

# 🔑 CONFIGURATION BYBIT

## Créer API Keys

1. Aller sur https://www.bybit.com/app/user/api-management
2. Cliquer "Create New Key"
3. Nom: "SmartOrder PRO"
4. Permissions:
   - ✅ Read/Write
   - ✅ Contract Trading
   - ✅ Spot Trading
   - ✅ Wallet
5. IP Whitelist: Ajouter IP de ton VPS (recommandé)
6. Copier API Key et Secret

⚠️ **IMPORTANT:** 
- Ne jamais partager tes API Keys
- Activer 2FA sur compte Bybit
- Utiliser IP Whitelist

---

# 🚀 LANCEMENT DES SERVICES

## Test Local (Windows)

### Méthode 1: Manuellement (plusieurs terminaux)

**Terminal 1:**
```powershell
python api/api_sentiment.py
```

**Terminal 2:**
```powershell
python api/api_mode.py
```

**Terminal 3:**
```powershell
python telegram/mode_handler.py
```

### Méthode 2: Script de lancement (à créer)

Créer `start_all.bat`:
```batch
@echo off
start "Sentiment API" python api/api_sentiment.py
start "Mode API" python api/api_mode.py
start "Telegram Bot" python telegram/mode_handler.py
echo Services démarrés !
pause
```

Double-cliquer pour lancer !

## Production (VPS)

```bash
# Démarrer tous les services
supervisorctl start all

# Arrêter tous les services
supervisorctl stop all

# Redémarrer un service
supervisorctl restart smartorder-mode

# Voir les logs
tail -f /var/log/smartorder-mode.out.log
```

---

# ✅ VÉRIFICATION

## 1. Vérifier APIs

### API Sentiment
```bash
curl http://localhost:8558/health
```

Résultat attendu:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T14:00:00"
}
```

### API Mode
```bash
curl http://localhost:8560/health
```

### API Suggestions
```bash
curl http://localhost:8560/api/mode/suggestions
```

## 2. Vérifier Interface Web

Ouvrir navigateur:
- Local: http://localhost/mode_switcher.html
- VPS: http://votre_ip_vps/mode_switcher.html

Tu dois voir:
- ✅ 4 boutons de modes
- ✅ Stratégie temps réel
- ✅ Liste coins recommandés

## 3. Vérifier Telegram

1. Ouvrir Telegram
2. Chercher ton bot
3. Envoyer `/start`
4. Envoyer `/mode`

Tu dois recevoir:
- ✅ Message de bienvenue
- ✅ 4 boutons de modes

---

# 🔧 TROUBLESHOOTING

## Problème: API ne démarre pas

### Vérifier le port
```bash
# Linux
netstat -tulpn | grep 8558

# Windows
netstat -an | findstr 8558
```

### Changer le port si occupé
Éditer le fichier API et changer:
```python
port=8558  # → port=8559
```

## Problème: Module non trouvé

```bash
pip install le_module_manquant
```

Modules nécessaires:
- fastapi
- uvicorn
- python-telegram-bot
- requests
- pybit
- websockets

## Problème: Erreur Bybit API

Vérifier:
1. ✅ API Keys correctes dans `.env`
2. ✅ Permissions API activées
3. ✅ IP Whitelist (si configuré)
4. ✅ Solde suffisant sur compte

## Problème: Telegram ne répond pas

1. Vérifier token dans `telegram/mode_handler.py`
2. Vérifier que le bot est démarré
3. Tester avec `/start`

## Problème: Interface Web ne charge pas

1. Vérifier que les APIs sont lancées
2. Ouvrir console navigateur (F12)
3. Vérifier les erreurs réseau
4. Vérifier l'URL de l'API dans `mode_switcher.html` ligne 342:
   ```javascript
   const API_BASE = 'http://localhost:8560';
   ```

---

# 📊 MONITORING

## Logs en temps réel

### Supervisor
```bash
supervisorctl tail -f smartorder-mode stdout
supervisorctl tail -f smartorder-sentiment stdout
```

### Nginx
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Vérifier santé des services

Script `check_health.sh`:
```bash
#!/bin/bash

echo "Checking APIs..."

# Sentiment API
curl -s http://localhost:8558/health | jq .

# Mode API
curl -s http://localhost:8560/health | jq .

echo "All checks done!"
```

---

# 🎯 RÉSUMÉ DES PORTS

| Service | Port | URL |
|---------|------|-----|
| API Sentiment | 8558 | http://localhost:8558 |
| API Mode | 8560 | http://localhost:8560 |
| API PnL | 8556 | http://localhost:8556 |
| API Signal Memory | 8557 | http://localhost:8557 |
| API Execution | 8559 | http://localhost:8559 |
| Interface Web | 80 | http://localhost |
| Interface Web SSL | 443 | https://localhost |

---

# 🔐 SÉCURITÉ

## Checklist Sécurité

- [ ] API Keys dans `.env` (pas dans le code)
- [ ] `.env` dans `.gitignore`
- [ ] IP Whitelist activé sur Bybit
- [ ] 2FA activé sur compte Bybit
- [ ] SSL/HTTPS configuré (production)
- [ ] Firewall configuré (ports 80, 443 uniquement)
- [ ] Mots de passe forts
- [ ] Backups réguliers

## Firewall VPS

```bash
# Installer UFW
apt install -y ufw

# Autoriser SSH
ufw allow 22/tcp

# Autoriser HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Activer
ufw enable
```

---

# 📝 COMMANDES UTILES

## Git

```bash
# Pull dernières modifications
git pull

# Vérifier status
git status

# Voir logs
git log --oneline -10
```

## Supervisor

```bash
# Status
supervisorctl status

# Démarrer
supervisorctl start smartorder-mode

# Arrêter
supervisorctl stop smartorder-mode

# Redémarrer
supervisorctl restart smartorder-mode

# Logs
supervisorctl tail -f smartorder-mode stdout
```

## Nginx

```bash
# Tester config
nginx -t

# Recharger
systemctl reload nginx

# Redémarrer
systemctl restart nginx

# Status
systemctl status nginx
```

---

# 🎉 FÉLICITATIONS !

Si tu arrives ici, ton bot SmartOrder PRO est:
- ✅ Déployé
- ✅ Fonctionnel
- ✅ Accessible 24/7 (si VPS)
- ✅ Sécurisé

**Tu peux maintenant:**
1. Utiliser l'interface Web
2. Contrôler via Telegram
3. Laisser l'IA gérer intelligemment
4. Profiter du mode HYBRID

---

# 📞 SUPPORT

**Problème ?**
1. Consulter les logs
2. Vérifier ce guide
3. Relire la documentation
4. Tester en local d'abord

**Tout marche ?**
🎊 **PROFITE DE TON BOT !** 🚀

---

**Version:** 1.0  
**Dernière mise à jour:** 2025-01-26  
**SmartOrder PRO v1.8-FINAL** 💪
