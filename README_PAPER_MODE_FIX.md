# 🚨 FIX RAPIDE - PAPER MODE SmartOrder PRO AI v2.1

## ⚡ CORRECTION EN 3 ÉTAPES

### 1️⃣ Exécuter le script de correction

```powershell
cd C:\Users\aimet\smartorder-pro-ai-v1.7
.\deploy_paper_mode_fix.ps1
```

**Confirmez avec `oui` quand demandé**

---

### 2️⃣ Vérifier le PnL pendant 3 minutes

```powershell
# Surveillance automatique
for ($i=1; $i -le 12; $i++) {
    $pnl = ssh root@107.189.22.255 "cat /opt/smartorder-pro/config/pnl_tracker.json | grep total_pnl"
    Write-Host "[$i/12] $pnl"
    Start-Sleep -Seconds 15
}
```

**✅ Le PnL DOIT évoluer**

---

### 3️⃣ Vérifier le Dashboard

🌐 **URL :** https://107.189.22.255/dashboard  
🔑 **Token :** `dev_token_12345`

**Sections à valider :**
- 💰 PnL évolue en temps réel
- 🧠 Diagnostic actif
- 🚨 Emergency controls fonctionnels

---

## 📊 COMMANDES RAPIDES

### Statut des services (SSH)
```bash
ssh root@107.189.22.255 "systemctl status smartorder-paper-engine smartorder-diagnostic --no-pager"
```

### Logs en direct
```bash
ssh root@107.189.22.255 "tail -f /opt/smartorder-pro/logs/paper_trades.log"
```

### PnL actuel
```bash
ssh root@107.189.22.255 "cat /opt/smartorder-pro/config/pnl_tracker.json"
```

---

## 🆘 PROBLÈMES COURANTS

### ❌ Connexion SSH échoue
```powershell
# Test de connexion
ssh root@107.189.22.255
# Si demande mot de passe, l'entrer
```

### ❌ PnL ne change pas
```bash
ssh root@107.189.22.255 "systemctl restart smartorder-paper-engine && sleep 30 && cat /opt/smartorder-pro/config/pnl_tracker.json"
```

### ❌ Service failed
```bash
ssh root@107.189.22.255 "journalctl -u smartorder-paper-engine -n 50"
```

---

## 📚 DOCUMENTATION COMPLÈTE

Voir : [GUIDE_PAPER_MODE_CORRECTION.md](docs/GUIDE_PAPER_MODE_CORRECTION.md)

---

## ✅ CHECKLIST SUCCÈS

- [ ] Script `deploy_paper_mode_fix.ps1` exécuté sans erreur
- [ ] Services `smartorder-paper-engine` et `smartorder-diagnostic` actifs
- [ ] PnL évolue automatiquement (vérifié sur 3 minutes)
- [ ] Dashboard accessible et fonctionnel
- [ ] Notification Telegram reçue

**🎯 Système Paper Mode opérationnel !**

---

**Contact :** MAIGA ABOUBACAR  
**Version :** 2.1  
**Date :** 2025-11-02
