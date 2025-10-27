# 🎯 GUIDE D'ORGANISATION - SmartOrder PRO
## by MAIGA ABOUBACAR

---

## ✅ CE QUI A ÉTÉ FAIT (Tasks 1-2)

### Task #1 : Executor auto-load .env ✅
- Ajout de `python-dotenv` pour charger automatiquement le .env
- Plus besoin de faire `export` manuellement
- Fichier : `executor/auto_executor.py`

### Task #2 : Trading Control connecté au vrai bot ✅  
- Création de `core/bot_state_manager.py` (237 lignes)
- Système de state centralisé dans `/opt/smartorder-pro/data/bot_state.json`
- API Trading Control (`api_trading_control.py`) maintenant connectée au vrai state
- Executor lit le state avant de trader
- **Sécurité** : Paper trading activé par défaut

---

## 📋 TÂCHES RESTANTES (Tasks 3-10)

### Task #3 : Afficher les vraies positions 

**Problème** : Le dashboard affiche des données vides  
**Solution** :
1. Dans `core/bybit_client.py`, fixer la fonction `futures_positions()`
2. Parser correctement la réponse Bybit V5 Unified
3. Mettre à jour le dashboard pour afficher les positions réelles

**Fichiers à modifier** :
- `core/bybit_client.py` (lignes 95-98)
- `web/portal_v5_pro/main_unified.py` (route `/api/futures_positions`)

---

### Task #4 : Intégrer le mode selector

**Objectif** : Ajouter une page `/modes` dans le dashboard principal (port 8555)

**Modes disponibles** :
- AUTO_SPOT - Trading automatique spot
- AUTO_FUTURES - Trading automatique futures
- MANUAL - Contrôle manuel
- HYBRID - Mix auto + manuel

**À faire** :
1. Le fichier `web/portal_v5_pro/templates/modes.html` existe déjà !
2. Ajouter la route dans `main_unified.py` :
```python
@app.get("/modes", response_class=HTMLResponse)
def modes_page(request: Request):
    return templates.TemplateResponse("modes.html", {"request": request})
```
3. Connecter aux APIs du mode manager (`ai/mode_manager.py`)

---

### Task #5 : Configurer les AI pour vrais signaux

**Problème** : `fusion_ai` génère toujours "neutral"

**Analyse** :
- Le fichier `/opt/smartorder/db/market_memory.json` contient le bias
- Les services AI tournent (fusion_ai, genetic_ai, behavior_ai, etc.)
- Mais ils ne génèrent pas de signaux bullish/bearish

**Solution** :
1. Vérifier les logs des services AI :
```bash
journalctl -u smartorder-fusion-ai.service -n 100
```
2. Vérifier la DB SQLite `/opt/smartorder/db/ai_memory.db`
3. Ajouter des données de test pour que l'AI génère des signaux
4. OU créer un mode "Simulation" qui génère des signaux artificiels pour tester

---

### Task #6 : Unifier les dashboards

**Problème** : 2 dashboards tournent en parallèle :
- Port 5000 (Flask - `web_dashboard.py`)
- Port 8555 (FastAPI - `web/portal_v5_pro/main_unified.py`)

**Solution** :
1. Arrêter le dashboard Flask (port 5000)
2. Tout migrer vers FastAPI (port 8555)
3. Le dashboard FastAPI a déjà presque tout :
   - ✅ Login JWT
   - ✅ Analytics
   - ✅ Trading Control
   - ❌ Manque juste les WebSockets (actuellement dans Flask)

**À faire** :
- Ajouter WebSocket support à FastAPI
- Supprimer ou désactiver `web_dashboard.py`

---

### Task #7 : Config centralisé

**Objectif** : Un seul fichier de config pour TOUT

**Créer** : `config/bot_config.json`
```json
{
  "trading": {
    "mode": "manual",
    "paper_trading": true,
    "exchange": "bybit",
    "risk_level": "low",
    "max_position_size": 100
  },
  "exchanges": {
    "bybit": {
      "enabled": true,
      "testnet": false
    },
    "binance": {
      "enabled": false
    }
  },
  "strategies": {
    "auto_spot": {
      "enabled": false,
      "coins": ["BTC", "ETH"]
    },
    "auto_futures": {
      "enabled": false,
      "leverage": 2
    }
  },
  "alerts": {
    "telegram": true,
    "email": false,
    "discord": false
  }
}
```

---

### Task #8 : Mode Paper Trading

**État actuel** : Le paper trading est activé par défaut dans `bot_state.json`

**À faire** :
1. Créer un module `core/paper_trading_engine.py`
2. Simuler les ordres sans appeler l'exchange réel
3. Sauvegarder les trades virtuels dans une DB
4. Afficher les résultats dans le dashboard

**Avantage** : Tester le bot sans risque avant d'activer le trading réel !

---

### Task #9 : Script de démarrage unique

**Objectif** : Un seul script pour démarrer TOUT

**Créer** : `start_bot.sh`
```bash
#!/bin/bash
# SmartOrder PRO - Démarrage automatique
# by MAIGA ABOUBACAR

echo "🚀 Démarrage SmartOrder PRO..."

# 1. Vérifier que le .env existe
if [ ! -f "/opt/smartorder-pro/.env" ]; then
    echo "❌ Fichier .env introuvable !"
    exit 1
fi

# 2. Créer les répertoires nécessaires
mkdir -p /opt/smartorder-pro/data
mkdir -p /opt/smartorder-pro/logs

# 3. Initialiser le state du bot
python -c "from core.bot_state_manager import get_state_manager; get_state_manager()"

# 4. Démarrer le dashboard FastAPI (port 8555)
echo "📊 Démarrage dashboard..."
nohup python -m uvicorn web.portal_v5_pro.main_unified:app --host 0.0.0.0 --port 8555 > logs/dashboard.log 2>&1 &

# 5. Vérifier que les services systemd sont actifs
echo "✅ Services AI:"
systemctl is-active smartorder-fusion-ai.service
systemctl is-active smartorder-genetic.service
systemctl is-active smartorder-behavior.service

echo "✅ Bot démarré !"
echo "Dashboard : https://votreip:8555"
```

---

### Task #10 : Documentation finale

**Créer** : `GUIDE_UTILISATION.md`

Contenu :
1. Installation (dépendances, .env)
2. Configuration (exchanges, API keys, modes)
3. Démarrage (script start_bot.sh)
4. Utilisation (dashboard, Telegram, API)
5. Monitoring (logs, health check)
6. Troubleshooting (erreurs courantes)
7. Sécurité (permissions API, paper trading)

---

## 🚀 PROCHAINE SESSION

**Commandes VPS** :
```bash
cd /opt/smartorder-pro
git pull
pip install python-dotenv  # Pour l'executor
python -c "from core.bot_state_manager import get_state_manager; print(get_state_manager().get_full_state())"
```

**Ordre recommandé** :
1. Task #3 (Positions réelles) - Critique
2. Task #4 (Mode selector) - Important  
3. Task #8 (Paper trading) - Pour tester
4. Task #9 (Script démarrage) - Facilite tout
5. Task #10 (Documentation) - Pour ne rien oublier

---

## 📊 PROGRÈS ACTUEL

✅ 2/10 tasks complétées (20%)  
⏱️ ~2-3h restantes pour finir les 8 autres  
🎯 Objectif : Bot 100% organisé et fonctionnel  

---

**Dernière mise à jour** : 27/10/2025 00:25  
**Commit** : f8aafecd  
**Statut** : En cours d'organisation 🔧
