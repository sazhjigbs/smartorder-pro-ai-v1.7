#!/usr/bin/env python3
import requests
import json

print("=" * 70)
print("🔍 VÉRIFICATION COMPLÈTE - SmartOrder PRO AI")
print("=" * 70)
print()

success_count = 0
total_tests = 0

# Test 1: APIs
print("1️⃣  TEST DES APIs")
print("-" * 70)

tests = [
    ("Stratégies SPOT", "https://localhost/api/strategies?mode=SPOT", "strategies"),
    ("Stratégies FUTURES", "https://localhost/api/strategies?mode=FUTURES", "strategies"),
    ("Exchanges", "https://localhost/api/exchanges", "exchanges"),
    ("Positions", "https://localhost/api/positions", "positions"),
]

for name, url, key in tests:
    total_tests += 1
    try:
        r = requests.get(url, verify=False, timeout=5)
        data = r.json()
        
        if key == "strategies":
            count = len(data.get("strategies", []))
            print(f"   ✅ {name:25s}: {count} disponibles")
            success_count += 1
        elif key == "exchanges":
            if isinstance(data, list):
                count = len(data)
            else:
                count = len(data.get("exchanges", []))
            print(f"   ✅ {name:25s}: {count} configurés")
            success_count += 1
        elif key == "positions":
            count = len(data) if isinstance(data, list) else 0
            print(f"   ✅ {name:25s}: {count} position(s)")
            success_count += 1
    except Exception as e:
        print(f"   ❌ {name:25s}: {str(e)[:40]}")

print()

# Test 2: Dashboard
print("2️⃣  TEST DASHBOARD")
print("-" * 70)
total_tests += 1

try:
    r = requests.get("https://localhost/dashboard", verify=False, timeout=5)
    if r.status_code == 200:
        size_kb = len(r.text) / 1024
        
        # Vérifier la présence des modules clés
        modules_found = 0
        modules = [
            "MODES DE TRADING",
            "Active Strategies",
            "Multi-Exchange Manager",
            "Emergency Controls",
            "Live Activity Log"
        ]
        
        for module in modules:
            if module in r.text:
                modules_found += 1
        
        print(f"   ✅ Dashboard accessible: {size_kb:.1f} KB")
        print(f"   ✅ Modules détectés: {modules_found}/{len(modules)}")
        success_count += 1
    else:
        print(f"   ⚠️  Dashboard: Status {r.status_code}")
except Exception as e:
    print(f"   ❌ Dashboard: {str(e)[:50]}")

print()

# Test 3: Configuration Nginx
print("3️⃣  TEST CONFIGURATION NGINX")
print("-" * 70)
total_tests += 1

try:
    with open('/etc/nginx/sites-available/safelogic', 'r') as f:
        nginx_conf = f.read()
    
    if 'location /api/' in nginx_conf and '127.0.0.1:8001' in nginx_conf:
        print("   ✅ Route /api/ vers port 8001 configurée")
        success_count += 1
    else:
        print("   ⚠️  Configuration /api/ à vérifier")
        
    if 'location /dashboard' in nginx_conf:
        print("   ✅ Route /dashboard configurée")
    
except Exception as e:
    print(f"   ❌ Lecture nginx: {str(e)[:50]}")

print()

# Test 4: Fichiers déployés
print("4️⃣  VÉRIFICATION FICHIERS")
print("-" * 70)

import os

files_to_check = [
    ('/opt/smartorder-pro/web/dashboard.html', 'Dashboard HTML'),
    ('/tmp/diagnostic_ultra_intelligent.py', 'Script diagnostic'),
]

for filepath, description in files_to_check:
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"   ✅ {description:25s}: {size} bytes")
    else:
        print(f"   ❌ {description:25s}: NON TROUVÉ")

print()

# Résumé final
print("=" * 70)
print(f"📊 RÉSUMÉ: {success_count}/{total_tests} tests réussis")
print("=" * 70)

if success_count == total_tests:
    print("✅ SYSTÈME ENTIÈREMENT OPÉRATIONNEL")
    print()
    print("🔗 Dashboard accessible à: https://107.189.22.255/dashboard")
else:
    print(f"⚠️  {total_tests - success_count} problème(s) détecté(s)")

print()
