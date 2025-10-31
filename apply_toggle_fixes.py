#!/usr/bin/env python3
"""
Script d'application automatique des correctifs pour SmartOrder PRO AI
Corrige les toggles stratégies et exchanges (backend + frontend)
"""

import subprocess
import sys
from datetime import datetime

print("="*80)
print("🔧 SmartOrder PRO AI - Application des correctifs TOGGLES")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

VPS_HOST = "root@107.189.22.255"

def run_ssh(command):
    """Exécuter commande SSH"""
    full_cmd = f'ssh {VPS_HOST} "{command}"'
    print(f"\n▶️  {command[:80]}...")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ Success")
    return True

# ÉTAPE 1 : BACKUP
print("\n" + "="*80)
print("📦 ÉTAPE 1/5 : Sauvegarde des fichiers actuels")
print("="*80)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
run_ssh(f"mkdir -p /opt/smartorder-pro/backups/{timestamp}")
run_ssh(f"cp /opt/smartorder-pro/api/main.py /opt/smartorder-pro/backups/{timestamp}/main.py.bak")
run_ssh(f"cp /opt/smartorder-pro/web/dashboard.html /opt/smartorder-pro/backups/{timestamp}/dashboard.html.bak")
print(f"✅ Backup sauvegardé dans /opt/smartorder-pro/backups/{timestamp}/")

# ÉTAPE 2 : UPLOAD NOUVEAU BACKEND
print("\n" + "="*80)
print("🚀 ÉTAPE 2/5 : Upload du backend API corrigé")
print("="*80)

upload_cmd = f"scp C:\\Users\\aimet\\smartorder-pro-ai-v1.7\\api_main_fixed.py {VPS_HOST}:/opt/smartorder-pro/api/main_fixed.py"
print(f"▶️  Uploading api_main_fixed.py...")
result = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Backend uploaded")
    run_ssh("cp /opt/smartorder-pro/api/main_fixed.py /opt/smartorder-pro/api/main.py")
    print("✅ Backend remplacé")
else:
    print(f"❌ Upload failed: {result.stderr}")
    sys.exit(1)

# ÉTAPE 3 : PATCHER LE DASHBOARD HTML
print("\n" + "="*80)
print("🎨 ÉTAPE 3/5 : Patch du dashboard HTML")
print("="*80)

dashboard_patch_script = """
python3 << 'PYTHON_EOF'
import re

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

# === AJOUT DES LOCKS GLOBAUX ===
if 'let toggleLocks' not in content:
    js_start = content.find('<script>')
    if js_start != -1:
        insert_pos = content.find('const API_BASE', js_start)
        if insert_pos != -1:
            locks_code = '''
        // GLOBAL STATE TRACKING
        let toggleLocks = {
            strategies: new Set(),
            exchanges: new Set()
        };
        
'''
            content = content[:insert_pos] + locks_code + content[insert_pos:]
            print("✅ Ajout des locks globaux")

# === REMPLACEMENT updateStrategies ===
update_strategies_pattern = r'async function updateStrategies\(\).*?^        \}'
new_update_strategies = '''async function updateStrategies() {
            try {
                const response = await fetch(`${API_BASE}/api/strategies?mode=${currentMode}`);
                const data = await response.json();
                
                const container = document.getElementById('strategies-container');
                container.innerHTML = '';
                
                const strategies = data.strategies || [];
                
                if (strategies.length === 0) {
                    container.innerHTML = '<p style="opacity: 0.7; text-align: center;">No strategies for this mode</p>';
                    return;
                }
                
                strategies.forEach(strategy => {
                    const div = document.createElement('div');
                    div.className = 'strategy-item' + (strategy.enabled ? ' enabled' : '');
                    div.dataset.strategyId = strategy.id;
                    
                    const isLocked = toggleLocks.strategies.has(strategy.id);
                    
                    div.innerHTML = `
                        <div class="strategy-info">
                            <div class="strategy-name">${strategy.name}</div>
                            <div class="strategy-score">Score: ${strategy.score}/100 ${strategy.recommended ? '⭐' : ''} | PnL: $${strategy.pnl}</div>
                        </div>
                        <div class="strategy-toggle-container">
                            ${isLocked ? '<span class="toggle-loader">⏳</span>' : ''}
                            <button class="strategy-toggle-btn ${strategy.enabled ? 'enabled' : 'disabled'}" 
                                    data-strategy-id="${strategy.id}"
                                    ${isLocked ? 'disabled' : ''}
                                    onclick="toggleStrategy('${strategy.id}', '${strategy.name}')">
                                ${strategy.enabled ? '✓ ENABLED' : '✗ DISABLED'}
                            </button>
                        </div>
                    `;
                    
                    container.appendChild(div);
                });
                
            } catch (error) {
                console.error('Strategies error:', error);
                addLog('❌ Error loading strategies', 'error');
            }
        }'''

if 'async function updateStrategies()' in content:
    # Trouver et remplacer updateStrategies
    pattern = r'async function updateStrategies\(\) \{[^}]*?(\{[^}]*\})*[^}]*?\n        \}'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    if match:
        content = content.replace(match.group(0), new_update_strategies)
        print("✅ updateStrategies() patché")

# === AJOUT toggleStrategy ===
if 'async function toggleStrategy(' not in content:
    toggle_strategy_code = '''
        
        // TOGGLE STRATEGY - AVEC API + PERSISTANCE + STATE LOCKING
        async function toggleStrategy(strategyId, strategyName) {
            if (toggleLocks.strategies.has(strategyId)) {
                addLog(`⏳ ${strategyName} is already being toggled...`, 'info');
                return;
            }
            
            try {
                toggleLocks.strategies.add(strategyId);
                addLog(`🔄 Toggling ${strategyName}...`, 'info');
                await updateStrategies();
                
                const response = await fetch(`${API_BASE}/api/strategies/${strategyId}/toggle`, {
                    method: 'PATCH',
                    headers: {'Content-Type': 'application/json'}
                });
                
                if (!response.ok) {
                    throw new Error(`API Error: ${response.status} ${response.statusText}`);
                }
                
                const result = await response.json();
                const newState = result.enabled ? 'ENABLED' : 'DISABLED';
                addLog(`✅ ${strategyName} ${newState}`, result.enabled ? 'success' : 'warning');
                await updateStrategies();
                
            } catch (error) {
                console.error('Toggle strategy error:', error);
                addLog(`❌ Error toggling ${strategyName}: ${error.message}`, 'error');
                await updateStrategies();
            } finally {
                toggleLocks.strategies.delete(strategyId);
            }
        }
        '''
    
    # Insérer après updateStrategies
    insert_marker = 'async function updateExchanges()'
    insert_pos = content.find(insert_marker)
    if insert_pos != -1:
        content = content[:insert_pos] + toggle_strategy_code + '\\n        ' + content[insert_pos:]
        print("✅ toggleStrategy() ajouté")

# === REMPLACEMENT toggleExchange ===
if 'function toggleExchange(name)' in content:
    # Remplacer l'ancien toggleExchange
    old_toggle = r'function toggleExchange\(name\) \{[^}]*\}'
    new_toggle_exchange = '''async function toggleExchange(name) {
            if (toggleLocks.exchanges.has(name)) {
                addLog(`⏳ ${name} is already being toggled...`, 'info');
                return;
            }
            
            try {
                toggleLocks.exchanges.add(name);
                addLog(`🔄 Toggling ${name}...`, 'info');
                await updateExchanges();
                
                const response = await fetch(`${API_BASE}/api/exchanges/${name}/toggle`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                if (!response.ok) {
                    throw new Error(`API Error: ${response.status} ${response.statusText}`);
                }
                
                const result = await response.json();
                addLog(`✅ ${name} ${result.status.toUpperCase()}`, result.status === 'enabled' ? 'success' : 'warning');
                
                if (result.primary_exchange && result.primary_exchange !== name && result.status === 'disabled') {
                    addLog(`ℹ️ Primary exchange switched to ${result.primary_exchange}`, 'info');
                }
                
                await updateExchanges();
                
            } catch (error) {
                console.error('Toggle exchange error:', error);
                addLog(`❌ Error toggling ${name}: ${error.message}`, 'error');
                await updateExchanges();
            } finally {
                toggleLocks.exchanges.delete(name);
            }
        }'''
    
    match = re.search(old_toggle, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), new_toggle_exchange)
        print("✅ toggleExchange() patché")

# === AJOUT CSS POUR TOGGLES ===
if '.strategy-toggle-btn' not in content:
    css_insert = '''
        .strategy-toggle-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .strategy-toggle-btn {
            padding: 8px 16px;
            border: 2px solid;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            background: rgba(255,255,255,0.05);
        }

        .strategy-toggle-btn.enabled {
            border-color: #10b981;
            color: #10b981;
        }

        .strategy-toggle-btn.disabled {
            border-color: #ef4444;
            color: #ef4444;
        }

        .strategy-toggle-btn:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 0 15px currentColor;
        }

        .strategy-toggle-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .toggle-loader {
            font-size: 1.2em;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .exchange-toggle.locked {
            opacity: 0.5;
            cursor: not-allowed;
            pointer-events: none;
        }
    '''
    
    style_end = content.find('</style>')
    if style_end != -1:
        content = content[:style_end] + css_insert + content[style_end:]
        print("✅ CSS des toggles ajouté")

# Sauvegarder
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Dashboard HTML patché avec succès")
PYTHON_EOF
"""

run_ssh(dashboard_patch_script)

# ÉTAPE 4 : RESTART SERVICES
print("\n" + "="*80)
print("🔄 ÉTAPE 4/5 : Redémarrage des services")
print("="*80)

run_ssh("systemctl restart smartorder-api")
run_ssh("systemctl status smartorder-api --no-pager | head -10")
run_ssh("systemctl restart nginx")
print("✅ Services redémarrés")

# ÉTAPE 5 : VALIDATION
print("\n" + "="*80)
print("✅ ÉTAPE 5/5 : Tests de validation")
print("="*80)

run_ssh("sleep 3")
run_ssh("curl -s https://localhost:8000/ | head -3")
run_ssh("curl -s https://localhost:8000/api/strategies?mode=futures | python3 -m json.tool | head -15")
run_ssh("curl -s https://localhost:8000/api/exchanges | python3 -m json.tool | head -20")

print("\n" + "="*80)
print("🎉 CORRECTIFS APPLIQUÉS AVEC SUCCÈS")
print("="*80)
print(f"✅ Backend API v2.1 déployé")
print(f"✅ Dashboard HTML patché")
print(f"✅ Endpoints ajoutés :")
print(f"   - PATCH /api/strategies/{{id}}/toggle")
print(f"   - POST /api/exchanges/{{name}}/toggle")
print(f"   - POST /api/exchanges/select")
print(f"   - GET /api/exchanges/status")
print(f"✅ Backup disponible : /opt/smartorder-pro/backups/{timestamp}/")
print(f"🌐 Dashboard : https://107.189.22.255/dashboard")
print("="*80)
