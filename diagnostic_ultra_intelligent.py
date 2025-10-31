#!/usr/bin/env python3
"""
🤖 DIAGNOSTIC INTELLIGENT ULTRA-COMPLET
SmartOrder PRO Dashboard - Analyse exhaustive et auto-correction

Ce script analyse :
- Tous les ports et services actifs
- Toutes les APIs et leurs réponses
- Configuration nginx
- Dashboard HTML/JS
- Propose des corrections automatiques
"""

import subprocess
import json
import requests
import re
from datetime import datetime
from collections import defaultdict

print('=' * 80)
print('🤖 DIAGNOSTIC INTELLIGENT ULTRA-COMPLET - SmartOrder PRO')
print('=' * 80)
print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

issues_found = []
corrections_proposed = []

# ============================================================================
# 1. AUDIT COMPLET DES PORTS VPS
# ============================================================================
print('1️⃣  AUDIT COMPLET DES PORTS VPS')
print('-' * 80)

result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
ports_info = {}

for line in result.stdout.split('\n'):
    if 'LISTEN' in line:
        match = re.search(r':(\d+)\s+.*users:\(\(\"([^\"]+)\"', line)
        if match:
            port = match.group(1)
            process = match.group(2)
            if port not in ports_info:
                ports_info[port] = []
            ports_info[port].append(process)

print(f'   📊 Ports en écoute: {len(ports_info)}')
for port, processes in sorted(ports_info.items(), key=lambda x: int(x[0])):
    print(f'   ✅ Port {port:5s} : {", ".join(set(processes))}')
print()

# Vérifier les ports critiques
critical_ports = {
    '80': 'HTTP (nginx)',
    '443': 'HTTPS (nginx)',
    '8000': 'API FastAPI',
    '8001': 'API Production',
}

for port, description in critical_ports.items():
    if port not in ports_info:
        issues_found.append(f'Port {port} ({description}) non actif')
        print(f'   ❌ Port {port} manquant : {description}')

print()

# ============================================================================
# 2. TEST EXHAUSTIF DES ENDPOINTS API
# ============================================================================
print('2️⃣  TEST EXHAUSTIF DES ENDPOINTS API')
print('-' * 80)

api_tests = [
    # Port 8000
    ('http://127.0.0.1:8000/api/exchanges', 'Port 8000', 'exchanges'),
    ('http://127.0.0.1:8000/api/strategies?mode=SPOT', 'Port 8000', 'strategies_spot'),
    ('http://127.0.0.1:8000/api/strategies?mode=FUTURES', 'Port 8000', 'strategies_futures'),
    ('http://127.0.0.1:8000/api/funding-rates', 'Port 8000', 'funding_rates'),
    ('http://127.0.0.1:8000/api/positions', 'Port 8000', 'positions'),
    
    # Port 8001
    ('http://127.0.0.1:8001/api/exchanges', 'Port 8001', 'exchanges'),
    ('http://127.0.0.1:8001/api/strategies?mode=SPOT', 'Port 8001', 'strategies_spot'),
    ('http://127.0.0.1:8001/api/strategies?mode=FUTURES', 'Port 8001', 'strategies_futures'),
    ('http://127.0.0.1:8001/api/funding-rates', 'Port 8001', 'funding_rates'),
    ('http://127.0.0.1:8001/api/positions', 'Port 8001', 'positions'),
]

api_results = {}
best_port_for = defaultdict(lambda: {'port': None, 'count': 0})

for url, port_label, endpoint_type in api_tests:
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        
        count = 0
        status = '✅'
        
        if 'strategies' in data:
            count = len(data.get('strategies', []))
        elif 'exchanges' in data:
            count = len(data.get('exchanges', []))
        elif isinstance(data, list):
            count = len(data)
        elif 'funding_rates' in data:
            count = len(data.get('funding_rates', []))
        
        if count == 0:
            status = '⚠️'
        
        print(f'   {status} {port_label:12s} - {endpoint_type:20s}: {count} items')
        
        api_results[f'{port_label}_{endpoint_type}'] = {
            'count': count,
            'status': r.status_code
        }
        
        # Déterminer le meilleur port pour chaque endpoint
        if count > best_port_for[endpoint_type]['count']:
            best_port_for[endpoint_type] = {'port': port_label, 'count': count}
            
    except Exception as e:
        print(f'   ❌ {port_label:12s} - {endpoint_type:20s}: ERREUR - {str(e)[:40]}')
        api_results[f'{port_label}_{endpoint_type}'] = {'count': 0, 'status': 'error'}

print()

# Analyse des résultats
print('   📊 ANALYSE DES RÉSULTATS:')
for endpoint_type, info in best_port_for.items():
    if info['count'] > 0:
        print(f'      {endpoint_type:20s} : Meilleur sur {info["port"]} ({info["count"]} items)')

print()

# ============================================================================
# 3. CONFIGURATION NGINX
# ============================================================================
print('3️⃣  CONFIGURATION NGINX')
print('-' * 80)

try:
    with open('/etc/nginx/sites-available/safelogic', 'r') as f:
        nginx_conf = f.read()
    
    # Vérifier location /api/
    has_api_location = 'location /api/' in nginx_conf
    
    if has_api_location:
        api_block = nginx_conf.split('location /api/')[1].split('location')[0]
        
        # Détecter vers quel port /api/ est routé
        port_match = re.search(r'proxy_pass.*:(\d+)', api_block)
        if port_match:
            api_port = port_match.group(1)
            print(f'   ✅ /api/ est routé vers le port {api_port}')
            
            # Vérifier si c'est le bon port
            best_strategies_port = best_port_for['strategies_spot']['port']
            if best_strategies_port and str(api_port) not in best_strategies_port:
                issues_found.append(f'/api/ route vers port {api_port} mais le meilleur est {best_strategies_port}')
                corrections_proposed.append({
                    'type': 'nginx',
                    'issue': f'API routée vers mauvais port ({api_port})',
                    'fix': f'Router /api/ vers port {best_strategies_port.split()[-1]}'
                })
                print(f'   ⚠️  PROBLÈME: Devrait router vers {best_strategies_port}')
        else:
            print('   ⚠️  Port de routing /api/ non détecté')
    else:
        issues_found.append('Pas de location /api/ dédiée dans nginx')
        print('   ❌ Pas de route /api/ dédiée')
        
except Exception as e:
    issues_found.append(f'Erreur lecture nginx: {e}')
    print(f'   ❌ Erreur: {e}')

print()

# ============================================================================
# 4. TEST ACCÈS PUBLIC (HTTPS)
# ============================================================================
print('4️⃣  TEST ACCÈS PUBLIC (HTTPS)')
print('-' * 80)

public_tests = [
    ('https://107.189.22.255/api/exchanges', 'Exchanges'),
    ('https://107.189.22.255/api/strategies?mode=SPOT', 'Strategies SPOT'),
    ('https://107.189.22.255/api/strategies?mode=FUTURES', 'Strategies FUTURES'),
    ('https://107.189.22.255/api/funding-rates', 'Funding Rates'),
]

public_working = True
for url, label in public_tests:
    try:
        r = requests.get(url, verify=False, timeout=10)
        data = r.json()
        
        count = 0
        if 'strategies' in data:
            count = len(data.get('strategies', []))
        elif 'exchanges' in data:
            count = len(data.get('exchanges', []))
        elif isinstance(data, list):
            count = len(data)
        
        if count > 0:
            print(f'   ✅ {label:25s}: {count} items')
        else:
            print(f'   ⚠️  {label:25s}: VIDE')
            public_working = False
            
    except Exception as e:
        print(f'   ❌ {label:25s}: ERREUR - {str(e)[:40]}')
        public_working = False
        issues_found.append(f'Accès HTTPS public échoue pour {label}')

print()

# ============================================================================
# 5. VÉRIFICATION DU DASHBOARD HTML
# ============================================================================
print('5️⃣  VÉRIFICATION DU DASHBOARD HTML')
print('-' * 80)

try:
    with open('/opt/smartorder-pro/web/dashboard.html', 'r') as f:
        dashboard_html = f.read()
    
    # Vérifier la présence des éléments critiques
    checks = {
        'fetch.*strategies': 'Appel API strategies',
        'fetch.*exchanges': 'Appel API exchanges',
        'fetch.*funding-rates': 'Appel API funding-rates',
        'strategies-list': 'Container liste stratégies',
        'exchanges.*container': 'Container exchanges',
    }
    
    for pattern, desc in checks.items():
        if re.search(pattern, dashboard_html, re.IGNORECASE):
            print(f'   ✅ {desc}')
        else:
            print(f'   ⚠️  {desc} - NON TROUVÉ')
            issues_found.append(f'Dashboard manque: {desc}')
    
except Exception as e:
    print(f'   ❌ Erreur lecture dashboard: {e}')
    issues_found.append(f'Impossible de lire dashboard.html')

print()

# ============================================================================
# RÉSUMÉ ET CORRECTIONS PROPOSÉES
# ============================================================================
print('=' * 80)
print('📋 RÉSUMÉ DU DIAGNOSTIC')
print('=' * 80)

if not issues_found:
    print('✅ AUCUN PROBLÈME DÉTECTÉ - Système opérationnel\n')
else:
    print(f'⚠️  {len(issues_found)} PROBLÈME(S) DÉTECTÉ(S):\n')
    for i, issue in enumerate(issues_found, 1):
        print(f'   {i}. {issue}')
    print()

if corrections_proposed:
    print('🔧 CORRECTIONS PROPOSÉES:\n')
    for i, correction in enumerate(corrections_proposed, 1):
        print(f'   {i}. Type: {correction["type"]}')
        print(f'      Problème: {correction["issue"]}')
        print(f'      Solution: {correction["fix"]}')
        print()

print('=' * 80)
print('✨ Fin du diagnostic intelligent')
print('=' * 80)
