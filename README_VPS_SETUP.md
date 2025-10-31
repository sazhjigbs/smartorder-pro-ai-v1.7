# 🚀 Configuration VPS - SmartOrder PRO

## ⚡ Démarrage Ultra-Rapide

### 1️⃣ Configuration Complète (une seule commande)

```powershell
.\setup_vps_complete.ps1 -VpsIp "VOTRE_IP_VPS"
```

**Exemple :**
```powershell
.\setup_vps_complete.ps1 -VpsIp "51.210.123.45"
```

**Ce que ça fait :**
- ✅ Configure SSH sans mot de passe (plus besoin de taper le mot de passe !)
- ✅ Déploie le script diagnostic intelligent sur VPS
- ✅ Lance une analyse complète du système
- ✅ Corrige automatiquement les erreurs détectées
- ✅ Génère un rapport détaillé

**Vous entrerez le mot de passe VPS UNE SEULE FOIS.**

---

### 2️⃣ Après la configuration

**Se connecter au VPS (sans mot de passe) :**
```powershell
ssh smartorder
```

**Lancer un diagnostic :**
```powershell
.\deploy_diagnostic_to_vps.ps1 -FixAll
```

**Monitoring continu 24/7 :**
```powershell
.\deploy_diagnostic_to_vps.ps1 -Watch -Interval 300
```

---

## 📖 Documentation Complète

Consultez le guide détaillé : [`GUIDE_SSH_DIAGNOSTIC_VPS.md`](GUIDE_SSH_DIAGNOSTIC_VPS.md)

---

## 🔧 Si SSH est déjà configuré

Si vous avez déjà configuré SSH :

```powershell
.\setup_vps_complete.ps1 -VpsIp "51.210.123.45" -SkipSshSetup
```

---

## 📊 Fonctionnalités du Diagnostic

- ✅ Détecte erreurs de compatibilité Python
- ✅ Trouve code incomplet (TODO, FIXME, pass, etc.)
- ✅ Compare stratégies configurées vs implémentées
- ✅ Vérifie cohérence entre modules
- ✅ **Corrige automatiquement** ce qui est réparable
- ✅ **Garde mémoire** des corrections pour éviter répétition
- ✅ Détecte oublis dans phases précédentes

---

## ⚙️ Scripts Disponibles

| Script | Description |
|--------|-------------|
| `setup_vps_complete.ps1` | Configuration complète tout-en-un |
| `setup_ssh_auto_login.ps1` | Configure uniquement SSH auto-login |
| `deploy_diagnostic_to_vps.ps1` | Déploie et exécute diagnostic |
| `smart_diagnostic_autocorrect.py` | Script diagnostic Python (pour VPS) |

---

## 🎯 Commandes Essentielles

```powershell
# Connexion SSH sans mot de passe
ssh smartorder

# Status du bot
ssh smartorder "systemctl status smartorder"

# Logs en direct
ssh smartorder "tail -f /opt/smartorder-pro/logs/trading.log"

# Redémarrer le bot
ssh smartorder "systemctl restart smartorder"

# Copier fichier vers VPS
scp mon_fichier.py smartorder:/opt/smartorder-pro/

# Récupérer rapport diagnostic
scp smartorder:/opt/smartorder-pro/smart_diagnostic_report.json .
```

---

**by MAIGA ABOUBACAR - SmartOrder PRO v1.7**
