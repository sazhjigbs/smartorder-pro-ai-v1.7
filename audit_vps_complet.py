#!/usr/bin/env python3
"""
Audit VPS Complet - SmartOrder PRO AI
Génère un rapport détaillé de tous les services, ports et modules actifs
"""
import subprocess
import json
import requests
from datetime import datetime

print("=" * 80)
print("🔍 AUDIT COMPLET VPS - SmartOrder PRO AI")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Résultats
audit_results = {
    "date": datetime.now().isoformat(),
    "ports": {},
    "services": {},
    "apis": {},
    "dashboard": {},
    "issues": []
}

# 1. SCAN COMPLET DES PORTS
print("1️⃣  SCAN COMPLET DES PORTS")
print("-" * 80)

result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
ports_found = {}

for line in result.stdout.split('\n'):
    if 'LISTEN' in line and ':' in line:
        try:
            parts = line.split()
            local_addr = parts[3]
            if ':' in local_addr:
                port = local_addr.split(':')[-1]
                # Extraire le nom du processus
                process = 'unknown'
                if 'users:' in line:
                    process_part = line.split('users:')[1]
                    if '((\"' in process_part:
                        process = process_part.split('((\"')[1].split('\"')[0]
                
                if port not in ports_found:
                    ports_found[port] = process
        except:
            pass

# Trier les ports par numéro
sorted_ports = sorted(ports_found.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 99999)

for port, process in sorted_ports:
    status = "✅" if process != "unknown" else "⚠️"
    print(f"   {status} Port {port:6s} : {process}")
    audit_results["ports"][port] = process

print(f"\n   📊 Total: {len(ports_found)} ports en écoute\n")

# 2. VÉRIFICATION DES PORTS CRITIQUES
print("2️⃣  PORTS CRITIQUES")
print("-" * 80)

critical_ports = {
    "22": "SSH",
    "80": "HTTP (nginx)",
    "443": "HTTPS (nginx)",
    "8000": "API FastAPI",
    "8001": "API Production",
    "8560": "API Mode"
}

for port, desc in critical_ports.items():
    if port in ports_found:
        print(f"   ✅ {desc:25s} : Port {port} actif")
    else:
        print(f"   ❌ {desc:25s} : Port {port} MANQUANT")
        audit_results["issues"].append(f"Port {port} ({desc}) non actif")

# Ports supplémentaires détectés
extra_ports = ["8091", "8088", "8787"]
extra_found = []
for port in extra_ports:
    if port in ports_found:
        extra_found.append(f"{port} ({ports_found[port]})")

if extra_found:
    print(f"\n   ℹ️  Ports supplémentaires: {', '.join(extra_found)}")

print()

# 3. TEST DES APIs
print("3️⃣  TEST DES ENDPOINTS API")
print("-" * 80)

api_tests = [
    ("Strategies SPOT", "https://localhost/api/strategies?mode=SPOT"),
    ("Strategies FUTURES", "https://localhost/api/strategies?mode=FUTURES"),
    ("Exchanges", "https://localhost/api/exchanges"),
    ("Positions", "https://localhost/api/positions"),
]

for name, url in api_tests:
    try:
        r = requests.get(url, verify=False, timeout=5)
        data = r.json()
        
        if "strategies" in data:
            count = len(data.get("strategies", []))
        elif isinstance(data, list):
            count = len(data)
        else:
            count = len(data.get("exchanges", []))
        
        print(f"   ✅ {name:25s} : {count} items")
        audit_results["apis"][name] = {"status": "OK", "count": count}
    except Exception as e:
        print(f"   ❌ {name:25s} : {str(e)[:40]}")
        audit_results["apis"][name] = {"status": "ERROR", "error": str(e)[:40]}
        audit_results["issues"].append(f"API {name} failed")

print()

# 4. VÉRIFICATION DASHBOARD
print("4️⃣  VÉRIFICATION DASHBOARD")
print("-" * 80)

try:
    r = requests.get("https://localhost/dashboard", verify=False, timeout=5)
    size_kb = len(r.text) / 1024
    
    # Modules à vérifier
    modules = {
        "MODES DE TRADING": False,
        "Active Strategies": False,
        "Multi-Exchange Manager": False,
        "Coins Watchlist": False,
        "Risk Management": False,
        "Emergency Controls": False,
        "Market Regime Detector": False,
        "MAIGA ABOUBAKR": False
    }
    
    for module in modules:
        if module in r.text:
            modules[module] = True
            print(f"   ✅ Module: {module}")
        else:
            print(f"   ❌ Module: {module} MANQUANT")
            audit_results["issues"].append(f"Dashboard module missing: {module}")
    
    modules_ok = sum(modules.values())
    print(f"\n   📊 Dashboard: {size_kb:.1f} KB, {modules_ok}/{len(modules)} modules détectés")
    audit_results["dashboard"] = {
        "size_kb": size_kb,
        "modules": modules,
        "modules_count": f"{modules_ok}/{len(modules)}"
    }
    
except Exception as e:
    print(f"   ❌ Dashboard: {str(e)[:50]}")
    audit_results["issues"].append(f"Dashboard error: {str(e)[:50]}")

print()

# 5. SERVICES PYTHON
print("5️⃣  SERVICES PYTHON ACTIFS")
print("-" * 80)

result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
python_processes = []

for line in result.stdout.split('\n'):
    if 'python' in line.lower() and 'smartorder' in line.lower():
        # Extraire les infos pertinentes
        parts = line.split()
        if len(parts) >= 11:
            cpu = parts[2]
            mem = parts[3]
            command = ' '.join(parts[10:])[:60]
            python_processes.append({
                "cpu": cpu,
                "mem": mem,
                "command": command
            })

for i, proc in enumerate(python_processes, 1):
    print(f"   {i}. CPU:{proc['cpu']}% MEM:{proc['mem']}% - {proc['command']}")
    
audit_results["services"]["python_count"] = len(python_processes)

print()

# 6. CONFIGURATION NGINX
print("6️⃣  CONFIGURATION NGINX")
print("-" * 80)

try:
    with open('/etc/nginx/sites-available/safelogic', 'r') as f:
        nginx_conf = f.read()
    
    checks = {
        "/api/ route": "location /api/" in nginx_conf and "8001" in nginx_conf,
        "/dashboard route": "location /dashboard" in nginx_conf,
        "SSL configuré": "ssl_certificate" in nginx_conf,
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            audit_results["issues"].append(f"Nginx: {check} failed")
    
except Exception as e:
    print(f"   ❌ Erreur lecture nginx: {str(e)[:40]}")

print()

# RÉSUMÉ FINAL
print("=" * 80)
print("📋 RÉSUMÉ DE L'AUDIT")
print("=" * 80)

issues_count = len(audit_results["issues"])

if issues_count == 0:
    print("✅ AUCUN PROBLÈME DÉTECTÉ")
    print("   Système entièrement opérationnel")
else:
    print(f"⚠️  {issues_count} PROBLÈME(S) DÉTECTÉ(S):")
    for i, issue in enumerate(audit_results["issues"], 1):
        print(f"   {i}. {issue}")

print()
print(f"📊 Statistiques:")
print(f"   - Ports actifs: {len(ports_found)}")
print(f"   - Services Python: {len(python_processes)}")
print(f"   - APIs fonctionnelles: {sum(1 for a in audit_results['apis'].values() if a.get('status') == 'OK')}/{len(api_tests)}")

print()
print("💾 Rapport sauvegardé")
print("=" * 80)

# Sauvegarder le rapport JSON
with open('/tmp/audit_vps_report.json', 'w') as f:
    json.dump(audit_results, f, indent=2)

print("\n📄 Rapport JSON: /tmp/audit_vps_report.json")
