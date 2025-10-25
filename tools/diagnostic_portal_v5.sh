#!/bin/bash
echo "=============================================================="
echo "🔍 DIAGNOSTIC GLOBAL — SAFELOGIC SmartOrder PRO Portal v5"
echo "Date : $(date)"
echo "=============================================================="

# Vérification structure globale
echo -e "\n📁 [1] Structure du projet :"
tree -L 3 /opt/smartorder-pro 2>/dev/null || ls -R /opt/smartorder-pro | head -n 40

# Vérification des fichiers init
echo -e "\n📦 [2] Vérification des fichiers __init__.py :"
find /opt/smartorder-pro -name "__init__.py"

# Vérification du contenu de sys.path dans Python
echo -e "\n🐍 [3] Test direct Python - Import modules core :"
python3 - <<'PY'
import sys, os
sys.path.insert(0, "/opt/smartorder-pro")
print("🔹 sys.path =", sys.path[:3])
try:
    import core.pnl_live
    print("✅ core.pnl_live importé avec succès.")
except Exception as e:
    print("❌ Erreur import core.pnl_live:", e)
try:
    import core.trust_memory_ai
    print("✅ core.trust_memory_ai importé avec succès.")
except Exception as e:
    print("❌ Erreur import core.trust_memory_ai:", e)
PY

# Vérification des dépendances FastAPI / Uvicorn
echo -e "\n📦 [4] Modules Python installés (FastAPI, Uvicorn, Requests) :"
pip3 show fastapi uvicorn requests | grep -E "Name|Version" || echo "❌ Modules manquants ou pip non fonctionnel"

# Vérification du service systemd (si configuré)
echo -e "\n⚙️ [5] Statut du service systemd smartorder-portal-v5 :"
systemctl status smartorder-portal-v5.service --no-pager | head -n 20

# Vérification des journaux récents
echo -e "\n🧾 [6] Derniers logs du service :"
journalctl -u smartorder-portal-v5.service -n 30 --no-pager | tail -n 30

# Vérification des ports réseau
echo -e "\n🌐 [7] État du port 8555 :"
sudo ss -tulpn | grep 8555 || echo "❌ Aucun service n'écoute sur le port 8555"

echo "=============================================================="
echo "✅ Diagnostic terminé — Analyse complète du portail"
echo "=============================================================="
