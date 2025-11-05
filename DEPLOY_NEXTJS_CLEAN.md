# 🚀 Déploiement Next.js SmartOrder PRO - MÉTHODE PROPRE

## ⚠️ IMPORTANT: NE PAS UTILISER POWERSHELL POUR L'ÉDITION DISTANTE

Les heredocs PowerShell → SSH corrompent les fichiers (.tsx avec backslashes).

**Méthodes fiables:**
- ✅ Git clone depuis le VPS
- ✅ SFTP/WinSCP upload
- ✅ Édition directe sur VPS (nano/vim)

---

## 📦 ÉTAPE 1: Préparer le repo local (Windows)

```powershell
cd C:\Users\aimet\smartorder-pro-ai-v1.7

# Créer branche production
git checkout -b nextjs-production

# Créer dossier Next.js
mkdir dashboard-nextjs-production
cd dashboard-nextjs-production

# Initialiser Next.js
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# Dépendances
npm install zustand @tanstack/react-query lucide-react

# Retour racine
cd ..

# Ajouter à git
git add dashboard-nextjs-production/
git commit -m "feat: Next.js production clean setup"
git push origin nextjs-production
```

---

## 🖥️ ÉTAPE 2: Déployer sur VPS (SSH direct)

**Connexion SSH (PuTTY/Terminal):**

```bash
# 1. Backup ancien dashboard
cd /opt/smartorder-pro
mv dashboard-nextjs dashboard-nextjs-OLD-$(date +%Y%m%d)

# 2. Clone branche production
git clone -b nextjs-production https://github.com/sazhjigbs/smartorder-pro-ai-v1.7.git dashboard-nextjs

# 3. Setup
cd dashboard-nextjs/dashboard-nextjs-production
npm install

# 4. Variables d'environnement
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://107.189.22.255:8091/api
NEXT_PUBLIC_WS_URL=ws://107.189.22.255:8182
EOF

# 5. Build production
npm run build

# 6. Démarrer avec PM2
pm2 delete smartorder-next 2>/dev/null || true
pm2 start npm --name smartorder-next -- start
pm2 save

# 7. Vérifier
pm2 logs smartorder-next --lines 20
curl -I http://localhost:3000
```

---

## 🔐 ÉTAPE 3: Configuration Nginx HTTPS

```bash
# Créer config Nginx
sudo nano /etc/nginx/sites-available/smartorder-nextjs
```

**Contenu:**

```nginx
server {
    listen 443 ssl http2;
    server_name 107.189.22.255;

    ssl_certificate /etc/ssl/certs/smartorder.crt;
    ssl_certificate_key /etc/ssl/private/smartorder.key;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8182;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}

server {
    listen 80;
    server_name 107.189.22.255;
    return 301 https://$host$request_uri;
}
```

**Activer:**

```bash
sudo ln -sf /etc/nginx/sites-available/smartorder-nextjs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## ✅ ÉTAPE 4: Vérification finale

```bash
# Ports
ss -ltnp | grep -E ":(22|443|3000|8091|8182)"

# Services
systemctl is-active smartorder-api smartorder-websocket nginx

# PM2
pm2 list

# Firewall
sudo ufw status numbered

# Test dashboard
curl -I https://107.189.22.255/
```

**Critères de succès:**
- ✅ `npm run build` → 0 erreur
- ✅ https://107.189.22.255/ → affiche Next.js
- ✅ Console F12 → 0 erreur JavaScript
- ✅ WebSocket reconnecte < 3s

---

## 📚 APIs Exchange (CCXT + SDKs officiels)

**Installation backend:**

```bash
pip install ccxt python-binance pybit python-kucoin okx
```

**Usage unifié (`/opt/smartorder-pro/api/exchanges/wallet.py`):**

```python
import ccxt

class UnifiedWallet:
    def __init__(self, exchange_name: str):
        self.exchange = getattr(ccxt, exchange_name)({
            'apiKey': os.getenv(f'{exchange_name.upper()}_API_KEY'),
            'secret': os.getenv(f'{exchange_name.upper()}_SECRET'),
        })
    
    def get_balance(self):
        return self.exchange.fetch_balance()
    
    def get_positions(self):
        return self.exchange.fetch_positions()
```

**SDKs dédiés (si CCXT insuffisant):**

- **Binance:** `from binance.client import Client`
- **Bybit UTA:** `from pybit.unified_trading import HTTP`
- **KuCoin:** `from kucoin.client import Client`
- **OKX:** `import okx.Account as Account`

---

## 📝 TODO LIST

- [ ] Push branche `nextjs-production` sur GitHub
- [ ] Clone sur VPS depuis SSH direct
- [ ] Build production zéro erreur
- [ ] Configuration Nginx HTTPS
- [ ] Intégration CCXT pour wallets multi-exchanges
- [ ] Tests fonctionnels (14 stratégies, watchlist, positions)
- [ ] Documentation VERIFY_REPORT.md

---

## 🆘 Support

Si problème de corruption fichiers:
1. ❌ **NE JAMAIS** éditer via PowerShell heredoc
2. ✅ Utiliser Git/SFTP/nano sur VPS
3. ✅ Vérifier encoding UTF-8 sans BOM
