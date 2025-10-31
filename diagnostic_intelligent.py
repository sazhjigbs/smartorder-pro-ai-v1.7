#!/usr/bin/env python3
"""
Diagnostic Intelligent - SmartOrder PRO Dashboard
Analyse complète du système pour identifier les problèmes
"""
import subprocess
import json
import requests
from datetime import datetime

print('🤖 DIAGNOSTIC INTELLIGENT - SmartOrder PRO Dashboard')
print('=' * 70)
print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# 1. Vérifier les services actifs
print('1️⃣  SERVICES BACKEND')
print('-' * 70)
result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
ports_status = {}
for port in ['8000', '8001', '443', '80']:
    if f':{port}' in result.stdout:
        print(f'   ✅ Port {port} en écoute')
        ports_status[port] = True
    else:
        print(f'   ❌ Port {port} NON disponible')
        ports_status[port] = False
print()

# 2. Tester les endpoints API
print('2️⃣  ENDPOINTS API')
print('-' * 70)
endpoints = [
    ('http://127.0.0.1:8000/api/exchanges', 'Port 8000 - Exchanges'),
    ('http://127.0.0.1:8000/api/strategies?mode=SPOT', 'Port 8000 - Strategies SPOT'),
    ('http://127.0.0.1:8000/api/strategies?mode=FUTURES', 'Port 8000 - Strategies FUTURES'),
    ('http://127.0.0.1:8001/api/exchanges', 'Port 8001 - Exchanges'),
    ('http://127.0.0.1:8001/api/strategies?mode=SPOT', 'Port 8001 - Strategies SPOT'),
    ('http://127.0.0.1:8001/api/strategies?mode=FUTURES', 'Port 8001 - Strategies FUTURES'),
]

api_results = {}
for url, desc in endpoints:
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if 'strategies' in data:
            count = len(data.get('strategies', []))
            print(f'   ✅ {desc}: {count} stratégies')
            api_results[desc] = count
        elif 'exchanges' in data:
            count = len(data.get('exchanges', []))
            print(f'   ✅ {desc}: {count} exchanges')
            api_results[desc] = count
        elif isinstance(data, list):
            print(f'   ✅ {desc}: {len(data)} items')
            api_results[desc] = len(data)
        else:
            print(f'   ⚠️  {desc}: réponse vide ou inattendue')
            api_results[desc] = 0
    except Exception as e:
        print(f'   ❌ {desc}: {str(e)[:50]}')
        api_results[desc] = None
print()

# 3. Vérifier nginx
print('3️⃣  CONFIGURATION NGINX')
print('-' * 70)
try:
    with open('/etc/nginx/sites-available/safelogic', 'r') as f:
        nginx_conf = f.read()
    
    has_api_location = 'location /api/' in nginx_conf
    
    if has_api_location:
        api_block = nginx_conf.split('location /api/')[1].split('location')[0]
        if '8001' in api_block:
            print('   ✅ /api/ route vers port 8001 (CORRECT)')
        elif '8000' in api_block:
            print('   ⚠️  /api/ route vers port 8000 (PROBLÈME: devrait être 8001)')
        else:
            print('   ⚠️  /api/ configuration non claire')
    else:
        print('   ⚠️  Pas de route /api/ dédiée')
        if '8000' in nginx_conf:
            print('      → Tout le trafic va vers port 8000 par défaut')
except Exception as e:
    print(f'   ❌ Erreur lecture nginx: {e}')
print()

# 4. Analyse et recommandations
print('4️⃣  ANALYSE & RECOMMANDATIONS')
print('-' * 70)

# Déterminer le bon port pour l'API
port_8000_strategies = api_results.get('Port 8000 - Strategies SPOT', 0)
port_8001_strategies = api_results.get('Port 8001 - Strategies SPOT', 0)

if port_8001_strategies and port_8001_strategies > 0:
    print('   🎯 PROBLÈME IDENTIFIÉ:')
    print(f'      - Port 8001 a {port_8001_strategies} stratégies disponibles')
    print(f'      - Port 8000 a {port_8000_strategies} stratégies')
    print('      - Nginx route actuellement vers le mauvais port!')
    print()
    print('   ✨ SOLUTION AUTOMATIQUE:')
    print('      Modifier nginx pour router /api/ vers port 8001')
    print()
    
    # Générer la correction
    correction_needed = True
else:
    print('   ✅ Configuration semble correcte')
    correction_needed = False

# 5. Test via HTTPS public
print('5️⃣  TEST ACCÈS PUBLIC')
print('-' * 70)
try:
    r = requests.get('https://107.189.22.255/api/strategies?mode=SPOT', 
                     verify=False, timeout=10)
    data = r.json()
    count = len(data.get('strategies', []))
    print(f'   {"✅" if count > 0 else "❌"} HTTPS public: {count} stratégies')
except Exception as e:
    print(f'   ❌ HTTPS public: {str(e)[:60]}')
print()

print('=' * 70)
if correction_needed:
    print('🔧 CORRECTION REQUISE - Exécuter fix_nginx.sh')
else:
    print('✅ SYSTÈME OPÉRATIONNEL')
print('=' * 70)
