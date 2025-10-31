# 🚀 Guide SSH Auto-Login + Diagnostic Automatique VPS

## 🎯 Objectif
- **Plus jamais de mot de passe SSH** à taper
- **Diagnostic automatique** du bot sur VPS
- **Corrections automatiques** des erreurs
- **Monitoring continu** 24/7

---

## 📋 Prérequis

- Windows avec PowerShell
- SSH client installé (inclus dans Windows 10+)
- Accès VPS avec mot de passe (pour la configuration initiale uniquement)

---

## ⚡ ÉTAPE 1 : Configuration SSH Auto-Login

### 1️⃣ Lancer la configuration (une seule fois)

```powershell
# Remplacez par votre IP VPS
.\setup_ssh_auto_login.ps1 -VpsIp "VOTRE_IP_VPS" -VpsUser "root"
```

**Exemple :**
```powershell
.\setup_ssh_auto_login.ps1 -VpsIp "51.210.123.45" -VpsUser "root"
```

### 2️⃣ Entrer le mot de passe VPS (pour la dernière fois)

Le script va :
- ✅ Générer une clé SSH sécurisée (RSA 4096 bits)
- ✅ Copier la clé sur le VPS
- ✅ Configurer l'auto-login
- ✅ Tester la connexion

### 3️⃣ C'est terminé !

Désormais, connectez-vous **SANS MOT DE PASSE** :

```powershell
ssh smartorder
```

---

## 🔍 ÉTAPE 2 : Diagnostic Automatique

### Mode 1️⃣ : Analyse Complète (une fois)

```powershell
.\deploy_diagnostic_to_vps.ps1 -FixAll
```

**Ce qu'il fait :**
- ✅ Copie le script diagnostic sur VPS
- ✅ Analyse tous les modules, fichiers, stratégies
- ✅ Détecte erreurs, doublons, code incomplet
- ✅ **Corrige automatiquement** ce qui est réparable
- ✅ Génère rapport JSON détaillé

### Mode 2️⃣ : Monitoring Continu 24/7

```powershell
.\deploy_diagnostic_to_vps.ps1 -Watch -Interval 300
```

**Ce qu'il fait :**
- 🔄 Vérifie l'état du bot **toutes les 5 minutes** (300s)
- 🔧 Corrige automatiquement les erreurs détectées
- 📊 Log toutes les corrections appliquées
- ⚠️ Alerte si problème critique

Pour **arrêter** le monitoring, faites `Ctrl+C` dans le terminal SSH.

---

## 📊 Récupérer le Rapport Diagnostic

```powershell
# Récupérer le rapport JSON
scp smartorder:/opt/smartorder-pro/smart_diagnostic_report.json .

# Lire le rapport
Get-Content smart_diagnostic_report.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 🛠️ Commandes Utiles

### Connexion SSH directe (sans mot de passe)
```powershell
ssh smartorder
```

### Exécuter une commande sur VPS sans se connecter
```powershell
ssh smartorder "cd /opt/smartorder-pro && systemctl status smartorder"
```

### Copier fichiers vers VPS
```powershell
scp mon_fichier.py smartorder:/opt/smartorder-pro/
```

### Copier fichiers depuis VPS
```powershell
scp smartorder:/opt/smartorder-pro/logs/bot.log ./logs/
```

### Voir logs en direct
```powershell
ssh smartorder "tail -f /opt/smartorder-pro/logs/trading.log"
```

### Redémarrer le bot
```powershell
ssh smartorder "systemctl restart smartorder"
```

---

## 🔧 Diagnostic Manuel sur VPS

Si vous voulez exécuter manuellement sur le VPS :

```bash
# Se connecter au VPS
ssh smartorder

# Aller dans le dossier bot
cd /opt/smartorder-pro

# Analyse complète avec corrections
python3 smart_diagnostic_autocorrect.py --fix-all

# Monitoring continu (Ctrl+C pour arrêter)
python3 smart_diagnostic_autocorrect.py --watch --interval 60

# Juste analyse sans correction
python3 smart_diagnostic_autocorrect.py
```

---

## 📈 Ce que Détecte le Diagnostic

### 1️⃣ **Compatibilité Python**
- ✅ Syntaxe incompatible
- ✅ Features Python 3.10+ dans code Python 3.8
- ✅ Modules obsolètes

### 2️⃣ **Code Incomplet**
- ⚠️ Fonctions avec juste `pass`
- ⚠️ TODO / FIXME non résolus
- ⚠️ `NotImplementedError`
- ⚠️ Classes vides

### 3️⃣ **Stratégies Manquantes**
- 📋 Compare config JSON vs implémentation réelle
- 📋 Détecte stratégies configurées mais non codées
- 📋 Liste modules manquants

### 4️⃣ **Cohérence Modules**
- 🔗 Vérifie imports entre modules
- 🔗 Détecte endpoints API manquants
- 🔗 Valide intégration des stratégies avancées

### 5️⃣ **Fichiers Dupliqués**
- 🗑️ **Supprime automatiquement** doublons
- 🗑️ Garde version dans `core/`, supprime `ai/`

### 6️⃣ **Progression vs État Réel**
- 📊 Compare `PROGRESS_TRACKER.json` vs code réel
- 📊 Détecte tâches marquées DONE mais non implémentées
- 📊 Alerte sur incohérences

---

## 🎯 Mémoire et Auto-Apprentissage

Le diagnostic garde **mémoire** de toutes les corrections :

```json
{
  "timestamp": "2025-10-29T18:30:00",
  "error_type": "duplicate_file",
  "file": "/opt/smartorder-pro/ai/signal_memory.py",
  "description": "Removed duplicate file",
  "fix_applied": "unlink()",
  "success": true
}
```

- 🧠 **Apprend** des corrections passées
- 🧠 **Évite** de répéter les mêmes erreurs
- 🧠 **Suggère** corrections similaires pour erreurs similaires

---

## 🚨 Troubleshooting

### Erreur : "Permission denied (publickey)"

**Problème :** Clé SSH non reconnue

**Solution :**
```powershell
# Re-lancer la configuration
.\setup_ssh_auto_login.ps1 -VpsIp "VOTRE_IP" -VpsUser "root"
```

### Erreur : "Connection timeout"

**Problème :** VPS inaccessible

**Solution :**
```powershell
# Vérifier connectivité
ping VOTRE_IP_VPS

# Vérifier service SSH
ssh root@VOTRE_IP_VPS "systemctl status sshd"
```

### Erreur : "smart_diagnostic_autocorrect.py not found"

**Problème :** Script non copié

**Solution :**
```powershell
# Copier manuellement
scp smart_diagnostic_autocorrect.py smartorder:/opt/smartorder-pro/
```

---

## 🎉 Résumé Ultra-Rapide

```powershell
# 1️⃣ Configuration SSH (une fois) - Remplacez l'IP
.\setup_ssh_auto_login.ps1 -VpsIp "51.210.123.45" -VpsUser "root"

# 2️⃣ Diagnostic complet avec corrections
.\deploy_diagnostic_to_vps.ps1 -FixAll

# 3️⃣ Monitoring continu 24/7 (optionnel)
.\deploy_diagnostic_to_vps.ps1 -Watch -Interval 300

# 4️⃣ Récupérer rapport
scp smartorder:/opt/smartorder-pro/smart_diagnostic_report.json .
```

---

## 🌟 Avantages

✅ **Plus jamais de mot de passe** à taper  
✅ **Diagnostic automatique** 24/7  
✅ **Corrections automatiques** des erreurs connues  
✅ **Mémoire intelligente** qui apprend  
✅ **Détection d'oublis** dans les phases passées  
✅ **Rapports détaillés** JSON  
✅ **Monitoring en temps réel**  

---

**by MAIGA ABOUBACAR - SmartOrder PRO**
