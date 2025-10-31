#!/usr/bin/env python3
"""
🧠 DIAGNOSTIC INTELLIGENT AVEC MÉMOIRE
SmartOrder PRO Dashboard - Détection intelligente et évitement de faux positifs

Ce module :
- Trace toutes les anomalies corrigées
- Évite les faux positifs lors des audits
- Vérifie la cohérence complète du bot
- Compare l'état réel vs référence
"""

import subprocess
import json
import requests
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "diag_memory.json"
VPS_IP = "188.245.188.145"

def load_memory():
    """Charge la mémoire du diagnostic"""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {
        "version": "1.0",
        "last_audit": None,
        "resolved_issues": [],
        "persistent_anomalies": [],
        "system_state": {},
        "corrections_history": []
    }

def save_memory(memory):
    """Sauvegarde la mémoire du diagnostic"""
    memory['last_audit'] = datetime.now().isoformat()
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def is_issue_resolved(issue_signature, memory):
    """Vérifie si une anomalie a déjà été corrigée"""
    return issue_signature in memory.get('resolved_issues', [])

def mark_issue_resolved(issue_signature, memory):
    """Marque une anomalie comme corrigée"""
    if issue_signature not in memory.get('resolved_issues', []):
        memory['resolved_issues'].append(issue_signature)

def check_systemd_services():
    """Vérifie les services systemd"""
    services = {
        'smartorder-ai-learner': {'port': 8000, 'type': 'AI Learner'},
        'smartorder-auto-executor': {'port': 8001, 'type': 'AutoExecutor'},
        'nginx': {'port': [80, 443], 'type': 'Nginx'}
    }
    
    results = {}
    
    for service_name, info in services.items():
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_active = result.stdout.strip() == 'active'
            results[service_name] = {
                'active': is_active,
                'port': info['port'],
                'type': info['type']
            }
        except Exception as e:
            results[service_name] = {
                'active': False,
                'port': info['port'],
                'type': info['type'],
                'error': str(e)
            }
    
    return results

def check_ports():
    """Vérifie les ports en écoute"""
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=5)
        ports_active = {}
        
        for port in [80, 443, 8000, 8001]:
            ports_active[port] = f':{port}' in result.stdout
        
        return ports_active
    except Exception as e:
        return {}

def check_api_endpoints(port):
    """Teste les endpoints API sur un port donné"""
    endpoints = [
        ('/api/exchanges', 'exchanges'),
        ('/api/strategies?mode=SPOT', 'strategies_spot'),
        ('/api/strategies?mode=FUTURES', 'strategies_futures'),
        ('/api/positions', 'positions'),
        ('/api/funding-rates', 'funding_rates')
    ]
    
    results = {}
    
    for endpoint, key in endpoints:
        try:
            url = f'http://127.0.0.1:{port}{endpoint}'
            r = requests.get(url, timeout=5)
            data = r.json()
            
            count = 0
            if 'strategies' in data:
                count = len(data.get('strategies', []))
            elif 'exchanges' in data:
                count = len(data.get('exchanges', []))
            elif isinstance(data, list):
                count = len(data)
            
            results[key] = {
                'status': r.status_code,
                'count': count,
                'working': True
            }
        except Exception as e:
            results[key] = {
                'status': 'error',
                'count': 0,
                'working': False,
                'error': str(e)[:50]
            }
    
    return results

def check_nginx_config():
    """Vérifie la configuration nginx"""
    try:
        with open('/etc/nginx/sites-available/safelogic', 'r') as f:
            nginx_conf = f.read()
        
        has_api_location = 'location /api/' in nginx_conf
        api_port = None
        
        if has_api_location:
            import re
            api_block = nginx_conf.split('location /api/')[1].split('location')[0]
            port_match = re.search(r'proxy_pass.*:(\d+)', api_block)
            if port_match:
                api_port = int(port_match.group(1))
        
        return {
            'has_api_location': has_api_location,
            'api_port': api_port,
            'valid': has_api_location and api_port is not None
        }
    except Exception as e:
        return {
            'has_api_location': False,
            'api_port': None,
            'valid': False,
            'error': str(e)
        }

def check_dashboard_files():
    """Vérifie la présence et intégrité des fichiers dashboard"""
    files_to_check = {
        '/opt/smartorder-pro/web/dashboard.html': 'Dashboard HTML',
        '/opt/smartorder-pro/web/dashboard_persistent_fix.js': 'Persistence Fix Script'
    }
    
    results = {}
    
    for file_path, description in files_to_check.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            results[description] = {
                'exists': True,
                'size': len(content),
                'valid': len(content) > 100  # Fichier non vide
            }
            
            # Vérifier si dashboard.html inclut le fix
            if 'dashboard.html' in file_path:
                results[description]['includes_fix'] = 'dashboard_persistent_fix.js' in content
        else:
            results[description] = {
                'exists': False,
                'size': 0,
                'valid': False
            }
    
    return results

def main():
    print('=' * 80)
    print('🧠 DIAGNOSTIC INTELLIGENT AVEC MÉMOIRE - SmartOrder PRO')
    print('=' * 80)
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    # Charger la mémoire
    memory = load_memory()
    print(f'📚 Mémoire chargée: {len(memory.get("resolved_issues", []))} issues résolues\n')
    
    issues = []
    warnings = []
    corrections = []
    
    # 1. Services systemd
    print('1️⃣  SERVICES SYSTEMD')
    print('-' * 80)
    services = check_systemd_services()
    
    for service_name, info in services.items():
        status_icon = '✅' if info['active'] else '❌'
        print(f'   {status_icon} {service_name:30s} : {info["type"]:20s} (Port {info["port"]})')
        
        if not info['active']:
            issue_sig = f'service_inactive_{service_name}'
            if not is_issue_resolved(issue_sig, memory):
                issues.append(f'Service {service_name} inactive')
                corrections.append({
                    'type': 'systemd',
                    'service': service_name,
                    'action': f'systemctl start {service_name}'
                })
    print()
    
    # 2. Ports en écoute
    print('2️⃣  PORTS EN ÉCOUTE')
    print('-' * 80)
    ports = check_ports()
    
    for port, is_active in ports.items():
        status_icon = '✅' if is_active else '❌'
        print(f'   {status_icon} Port {port}')
        
        if not is_active:
            issue_sig = f'port_inactive_{port}'
            if not is_issue_resolved(issue_sig, memory):
                issues.append(f'Port {port} non actif')
    print()
    
    # 3. Endpoints API
    print('3️⃣  ENDPOINTS API')
    print('-' * 80)
    
    best_port = None
    best_count = 0
    
    for port in [8000, 8001]:
        print(f'   Port {port}:')
        api_results = check_api_endpoints(port)
        
        total_count = sum(r['count'] for r in api_results.values())
        
        for key, result in api_results.items():
            status_icon = '✅' if result['working'] and result['count'] > 0 else '⚠️'
            print(f'      {status_icon} {key:20s}: {result["count"]} items')
        
        if total_count > best_count:
            best_count = total_count
            best_port = port
        
        print()
    
    if best_port:
        print(f'   🎯 Meilleur port pour API: {best_port} ({best_count} items totaux)\n')
    
    # 4. Configuration Nginx
    print('4️⃣  CONFIGURATION NGINX')
    print('-' * 80)
    nginx_config = check_nginx_config()
    
    if nginx_config['valid']:
        print(f'   ✅ Configuration valide - API routée vers port {nginx_config["api_port"]}')
        
        if best_port and nginx_config['api_port'] != best_port:
            issue_sig = f'nginx_wrong_port_{nginx_config["api_port"]}_{best_port}'
            if not is_issue_resolved(issue_sig, memory):
                issues.append(f'Nginx route vers port {nginx_config["api_port"]}, devrait être {best_port}')
                corrections.append({
                    'type': 'nginx',
                    'current_port': nginx_config['api_port'],
                    'target_port': best_port,
                    'action': 'Reconfigurer nginx pour router /api/ vers le bon port'
                })
            print(f'   ⚠️  PROBLÈME: Devrait router vers port {best_port}')
    else:
        print(f'   ❌ Configuration invalide')
        issues.append('Configuration nginx invalide')
    print()
    
    # 5. Fichiers Dashboard
    print('5️⃣  FICHIERS DASHBOARD')
    print('-' * 80)
    dashboard_files = check_dashboard_files()
    
    for file_desc, info in dashboard_files.items():
        status_icon = '✅' if info['valid'] else '❌'
        print(f'   {status_icon} {file_desc:30s}: {info["size"]} bytes')
        
        if not info['valid']:
            issue_sig = f'dashboard_file_missing_{file_desc}'
            if not is_issue_resolved(issue_sig, memory):
                issues.append(f'{file_desc} manquant ou invalide')
        
        if file_desc == 'Dashboard HTML' and 'includes_fix' in info:
            if not info['includes_fix']:
                issue_sig = 'dashboard_missing_fix_script'
                if not is_issue_resolved(issue_sig, memory):
                    issues.append('dashboard.html ne charge pas dashboard_persistent_fix.js')
                    corrections.append({
                        'type': 'dashboard',
                        'action': 'Injecter <script src="dashboard_persistent_fix.js"></script> dans dashboard.html'
                    })
                print('   ❌ dashboard.html NE CHARGE PAS le script de persistance!')
            else:
                print('   ✅ Script de persistance correctement inclus')
    print()
    
    # Résumé
    print('=' * 80)
    print('📋 RÉSUMÉ DU DIAGNOSTIC')
    print('=' * 80)
    
    if not issues:
        print('✅ AUCUN PROBLÈME DÉTECTÉ - Système opérationnel\n')
    else:
        print(f'⚠️  {len(issues)} PROBLÈME(S) NOUVEAU(X) DÉTECTÉ(S):\n')
        for i, issue in enumerate(issues, 1):
            print(f'   {i}. {issue}')
        print()
    
    if corrections:
        print('🔧 CORRECTIONS PROPOSÉES:\n')
        for i, correction in enumerate(corrections, 1):
            print(f'   {i}. Type: {correction["type"]}')
            print(f'      Action: {correction["action"]}')
            print()
    
    # Sauvegarder la mémoire
    memory['system_state'] = {
        'services': services,
        'ports': ports,
        'nginx': nginx_config,
        'dashboard': dashboard_files,
        'best_api_port': best_port
    }
    save_memory(memory)
    
    print('💾 Mémoire sauvegardée')
    print('=' * 80)
    
    return len(issues) == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
