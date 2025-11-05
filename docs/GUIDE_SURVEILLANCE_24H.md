# 📊 Guide de Surveillance 24h - Mode PAPER

**SmartOrder PRO AI v2.4 - SAFELOGIC**  
**Phase 6 → Phase 7 Transition**

---

## 🎯 Objectif

Valider la stabilité du système en mode PAPER pendant 24h minimum avant d'activer le trading REAL.

---

## ✅ Checklist de Surveillance

### 1️⃣ **Surveillance des Logs (Continue)**

#### Logs en temps réel
```bash
ssh root@107.189.22.255
tail -f /opt/smartorder-pro/logs/api_v24.log
```

#### Points à surveiller
- ✅ Aucune erreur critique
- ✅ Connexions stables aux exchanges
- ✅ Stratégies s'exécutent correctement
- ✅ Pas de crash ou redémarrage
- ✅ Temps de réponse API < 2s

---

### 2️⃣ **Tests API (Toutes les 4h)**

#### Health Check
```bash
curl -s http://107.189.22.255:8091/api/health | python3 -m json.tool
```

**Résultat attendu :**
```json
{
  "status": "ok",
  "version": "2.4",
  "service": "SmartOrder PRO AI"
}
```

#### Status Check
```bash
curl -s http://107.189.22.255:8091/api/status | python3 -m json.tool
```

**Résultat attendu :**
```json
{
  "status": "running",
  "mode": "paper",
  "version": "2.4"
}
```

#### Exchanges Check
```bash
curl -s http://107.189.22.255:8091/api/exchanges | python3 -m json.tool
```

---

### 3️⃣ **Vérification Dashboard (Toutes les 2h)**

Ouvrir dans le navigateur :
```
http://107.189.22.255:8181
```

#### Points à vérifier
- ✅ Dashboard accessible sans erreur 404
- ✅ Refresh automatique fonctionne (30s)
- ✅ Statut système : **opérationnel**
- ✅ Exchanges : **connectés**
- ✅ Mode : **PAPER**

---

### 4️⃣ **Service Systemd (Toutes les 6h)**

```bash
ssh root@107.189.22.255
systemctl status smartorder-api-v24 --no-pager
```

#### Indicateurs clés
- **Active:** `active (running)` ✅
- **Memory:** < 500MB ✅
- **Uptime:** Continu sans redémarrage ✅
- **Logs:** Pas d'erreurs critiques ✅

---

### 5️⃣ **Ressources Système (Toutes les 8h)**

```bash
ssh root@107.189.22.255
/opt/smartorder-pro/tools/monitor.sh
```

#### Métriques à surveiller
- **CPU:** < 80% en moyenne
- **RAM:** < 70% utilisée
- **Disk:** > 90GB libres
- **Network:** Latence stable vers exchanges

---

### 6️⃣ **Stratégies de Trading (Toutes les 12h)**

```bash
curl -s http://107.189.22.255:8091/api/strategies?mode=SPOT | python3 -m json.tool
```

#### Validation
- ✅ Au moins 2 stratégies actives
- ✅ Stratégies chargées sans erreur
- ✅ Paramètres cohérents

---

## 📈 Journal de Surveillance

### Modèle de log à tenir (format Excel/Google Sheets)

| Heure | Health Check | Status | Dashboard | Service | Logs | Observations |
|-------|-------------|--------|-----------|---------|------|--------------|
| 10:00 | ✅ OK | ✅ PAPER | ✅ Accessible | ✅ Running | ✅ Propre | RAS |
| 12:00 | ✅ OK | ✅ PAPER | ✅ Accessible | ✅ Running | ✅ Propre | RAS |
| 14:00 | ✅ OK | ✅ PAPER | ✅ Accessible | ✅ Running | ⚠️ Warning x1 | Connection timeout Bybit (récupéré) |
| ... | ... | ... | ... | ... | ... | ... |

---

## 🚨 Alertes et Actions

### ⚠️ Warning (Non bloquant)

**Symptômes :**
- Timeout ponctuel exchange (< 3 par jour)
- Latence API > 2s (< 5 fois par jour)
- Memory usage > 70% (temporaire)

**Actions :**
- Noter dans le journal
- Continuer la surveillance
- Si répétitif : investiguer

---

### ❌ Critique (Bloquant pour Phase 7)

**Symptômes :**
- Service crash ou redémarre
- Erreurs API répétées (> 10/h)
- Dashboard inaccessible > 5min
- Mode passe à REAL sans autorisation
- Perte connexion exchange > 30min

**Actions :**
1. **Arrêter immédiatement :**
   ```bash
   systemctl stop smartorder-api-v24
   ```

2. **Analyser les logs :**
   ```bash
   tail -100 /opt/smartorder-pro/logs/api_v24_error.log
   ```

3. **Investiguer et corriger**

4. **Relancer Phase 6 :**
   ```bash
   systemctl start smartorder-api-v24
   # Recommencer surveillance 24h
   ```

---

## ✅ Critères de Validation Phase 7

Avant de passer en mode REAL, **TOUS** ces critères doivent être remplis :

### Stabilité Système
- [ ] 24h+ sans crash ni redémarrage
- [ ] Uptime 100%
- [ ] < 5 warnings non critiques
- [ ] 0 erreur critique

### Performance
- [ ] API response time < 2s (moyenne)
- [ ] Memory stable < 500MB
- [ ] CPU < 80% (moyenne)

### Fonctionnalités
- [ ] Dashboard accessible 24/24
- [ ] API endpoints répondent
- [ ] Stratégies se chargent
- [ ] Connexions exchanges stables

### Configuration
- [ ] Clés API REAL configurées
- [ ] Guardian actif et testé
- [ ] Limites de risque validées
- [ ] Notifications Telegram fonctionnelles (si activées)

### Documentation
- [ ] Journal de surveillance complété
- [ ] Backup pré-REAL créé
- [ ] Procédure rollback testée

---

## 🔧 Commandes Utiles

### Surveillance rapide complète
```bash
ssh root@107.189.22.255 << 'EOF'
echo "=== SmartOrder PRO - Quick Status ==="
echo ""
echo "1. Service Status:"
systemctl is-active smartorder-api-v24 && echo "✅ RUNNING" || echo "❌ STOPPED"
echo ""
echo "2. API Health:"
curl -s http://localhost:8091/api/health | python3 -m json.tool
echo ""
echo "3. Last 10 log lines:"
tail -10 /opt/smartorder-pro/logs/api_v24.log
echo ""
echo "4. Memory Usage:"
free -h | grep Mem
echo ""
echo "5. Disk Space:"
df -h /opt/smartorder-pro | tail -1
EOF
```

### Redémarrage sécurisé (si nécessaire)
```bash
ssh root@107.189.22.255
systemctl restart smartorder-api-v24
sleep 5
systemctl status smartorder-api-v24 --no-pager
curl -s http://localhost:8091/api/health
```

### Export des logs pour analyse
```bash
ssh root@107.189.22.255
cd /opt/smartorder-pro/logs
tar -czf logs_export_$(date +%Y%m%d_%H%M%S).tar.gz *.log
# Puis télécharger avec scp si besoin
```

---

## 📧 Rapport de Validation 24h

Après 24h de surveillance, compléter ce rapport :

```
╔════════════════════════════════════════════════════════════════╗
║  RAPPORT DE VALIDATION 24H - MODE PAPER                        ║
║  SmartOrder PRO AI v2.4                                        ║
╚════════════════════════════════════════════════════════════════╝

Date début: _____________________
Date fin:   _____________________

┌─────────────────────────────────────────────────────────────┐
│ STABILITÉ                                                   │
├─────────────────────────────────────────────────────────────┤
│ Uptime:              _____ % (objectif: 100%)               │
│ Crashes:             _____ (objectif: 0)                    │
│ Redémarrages:        _____ (objectif: 0)                    │
│ Erreurs critiques:   _____ (objectif: 0)                    │
│ Warnings:            _____ (objectif: < 5)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PERFORMANCE                                                 │
├─────────────────────────────────────────────────────────────┤
│ API response avg:    _____ ms (objectif: < 2000)            │
│ Memory usage avg:    _____ MB (objectif: < 500)             │
│ CPU usage avg:       _____ % (objectif: < 80)               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ FONCTIONNALITÉS                                             │
├─────────────────────────────────────────────────────────────┤
│ Dashboard accessible:    [ ] OUI  [ ] NON                   │
│ API fonctionnelle:       [ ] OUI  [ ] NON                   │
│ Stratégies actives:      [ ] OUI  [ ] NON                   │
│ Exchanges connectés:     [ ] OUI  [ ] NON                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PRÉPARATION PHASE 7                                         │
├─────────────────────────────────────────────────────────────┤
│ Clés API REAL:           [ ] Configurées                    │
│ Guardian:                [ ] Validé                          │
│ Backup:                  [ ] Créé                            │
│ Rollback:                [ ] Testé                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DÉCISION                                                    │
├─────────────────────────────────────────────────────────────┤
│ [ ] ✅ GO pour Phase 7 - Passage REAL                       │
│ [ ] ⏳ NO-GO - Continuer surveillance                       │
│ [ ] ❌ NO-GO - Corrections nécessaires                      │
└─────────────────────────────────────────────────────────────┘

Observations complémentaires:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

Validé par: _____________________
Date:       _____________________
```

---

## 🚀 Passage à Phase 7

Une fois **TOUS** les critères validés :

```bash
ssh root@107.189.22.255
bash /opt/smartorder-pro/tools/execute_phase7_real.sh
```

**Le script demandera plusieurs confirmations pour sécurité maximale.**

---

**IMPORTANT :** Ne pas précipiter le passage en mode REAL. Mieux vaut 48h de tests PAPER que des pertes financières.

---

**Powered by SAFELOGIC - Intelligence & Sécurité Intégrées**
