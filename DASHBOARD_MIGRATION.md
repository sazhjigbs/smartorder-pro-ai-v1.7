# 🔄 Dashboard Migration Guide
## by MAIGA ABOUBACAR

---

## ✅ État Actuel

**Dashboard Unifié FastAPI (port 8555)** est maintenant le dashboard principal et complet avec toutes les features:

- ✅ Login JWT authentification
- ✅ Analytics temps réel
- ✅ Trading Control (Start/Stop/Pause/Emergency)
- ✅ Mode Selector (AUTO_SPOT, AUTO_FUTURES, MANUAL, HYBRID)
- ✅ Positions réelles affichées
- ✅ PNL Live tracking
- ✅ Execution Engine intégré
- ✅ Signals Memory
- ✅ Charts TradingView

---

## 🛑 Dashboard Flask (port 5000) - À DÉSACTIVER

Le vieux dashboard Flask peut maintenant être désactivé car tout est dans FastAPI.

### Comment désactiver le Flask dashboard:

#### 1. Arrêter le processus

```bash
# Sur le VPS
# Trouver le processus Flask
ps aux | grep web_dashboard

# Tuer le processus
kill -9 <PID>

# Ou arrêter le service systemd si configuré
sudo systemctl stop smartorder-flask-dashboard.service
sudo systemctl disable smartorder-flask-dashboard.service
```

#### 2. Empêcher le redémarrage automatique

Si le dashboard Flask démarre via systemd:

```bash
# Désactiver le service
sudo systemctl disable smartorder-flask-dashboard.service

# Supprimer le fichier service
sudo rm /etc/systemd/system/smartorder-flask-dashboard.service

# Recharger systemd
sudo systemctl daemon-reload
```

#### 3. (Optionnel) Supprimer le fichier Flask

Le fichier `web_dashboard.py` peut être conservé comme backup ou supprimé:

```bash
# Renommer pour backup
mv web/web_dashboard.py web/web_dashboard.py.old

# Ou supprimer
rm web/web_dashboard.py
```

---

## 🚀 Utiliser uniquement le Dashboard FastAPI

### Démarrage

```bash
cd /opt/smartorder-pro

# Option 1: Script automatique (recommandé)
./start_bot.sh

# Option 2: Manuel
python3 -m uvicorn web.portal_v5_pro.main_unified:app --host 0.0.0.0 --port 8555
```

### Accès

```
http://votre-ip:8555
```

### Features disponibles

| Feature | URL | Status |
|---------|-----|--------|
| Dashboard principal | `/` | ✅ |
| Login | `/login` | ✅ |
| Analytics | `/analytics` | ✅ |
| Trading Control | `/trading` | ✅ |
| Mode Selector | `/modes` | ✅ |
| PNL Live | `/api/pnl/live` | ✅ |
| Signals | `/api/signals/memory` | ✅ |

---

## 🔌 WebSocket Support (si nécessaire)

Le dashboard FastAPI supporte déjà WebSocket. Pour l'activer:

### 1. Installer la dépendance

```bash
pip install websockets
```

### 2. Ajouter le endpoint WebSocket dans `main_unified.py`

```python
from fastapi import WebSocket

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Envoyer données live
            data = {
                "positions": futures_positions(),
                "pnl": get_pnl_data(),
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(data)
            await asyncio.sleep(2)  # Update toutes les 2 secondes
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

### 3. Client JavaScript

```javascript
// Dans le HTML
const ws = new WebSocket('ws://your-ip:8555/ws/live');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Live update:', data);
    // Update UI
};
```

---

## ✅ Avantages du Dashboard Unifié

1. **Single Port** - Un seul port à ouvrir (8555)
2. **Performance** - FastAPI est plus rapide que Flask
3. **Moderne** - Async/await, WebSocket natif
4. **Sécurisé** - JWT auth intégré
5. **Complet** - Toutes les features en un seul endroit
6. **Maintenable** - Un seul codebase à gérer

---

## 📝 Notes

- Le port 5000 peut être libéré et utilisé pour autre chose
- Les anciennes URLs Flask ne fonctionneront plus
- Mettre à jour les bookmarks vers `http://ip:8555`
- Les bots Telegram doivent pointer vers les nouvelles APIs

---

**Migration complétée le**: 2025-01-27  
**Dashboard principal**: FastAPI (port 8555)  
**Dashboard Flask**: Désactivé ✅
