#!/usr/bin/env python3
"""
Fix Dashboard Final - Activity Log + Total PnL
===============================================
Ajoute updateActivityLog() et les appels dans periodicRefresh
"""

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajouter fonction updateActivityLog après updateTotalPnL
activity_log_function = '''

        // UPDATE ACTIVITY LOG (Live)
        async function updateActivityLog() {
            try {
                const response = await fetch(`${API_BASE}/api/activity-log`);
                const activities = await response.json();
                
                const logContainer = document.getElementById('activity-log');
                if (!logContainer) return;
                
                // Garder seulement les 20 dernières
                logContainer.innerHTML = '';
                
                activities.slice(-20).reverse().forEach(activity => {
                    const entry = document.createElement('div');
                    const msg = activity.message;
                    
                    let type = 'info';
                    if (msg.includes('BUY') || msg.includes('🟢')) type = 'success';
                    else if (msg.includes('SELL') || msg.includes('🔴')) type = 'warning';
                    else if (msg.includes('ERROR') || msg.includes('❌')) type = 'error';
                    
                    entry.className = 'log-entry log-' + type;
                    entry.textContent = msg;
                    logContainer.appendChild(entry);
                });
                
                console.log('📋 Activity Log:', activities.length, 'entries');
                
            } catch (error) {
                console.error('❌ Activity Log error:', error);
            }
        }'''

# Insérer après UPDATE MARKET REGIME
if 'UPDATE ACTIVITY LOG' not in content:
    content = content.replace(
        '        // UPDATE MARKET REGIME\n        async function updateMarketRegime()',
        activity_log_function + '\n\n        // UPDATE MARKET REGIME\n        async function updateMarketRegime()'
    )

# 2. Ajouter appel dans periodicRefresh
if 'await updateActivityLog()' not in content:
    content = content.replace(
        'await updateTotalPnL();  // Total PnL cumulatif',
        '''await updateTotalPnL();  // Total PnL cumulatif
        await updateActivityLog();  // Live Activity Log'''
    )

# 3. Ajouter appel initial au chargement
if 'setTimeout(loadInitialStates, 1000);' in content:
    content = content.replace(
        'setTimeout(loadInitialStates, 1000);',
        '''setTimeout(loadInitialStates, 1000);
setTimeout(updateTotalPnL, 2000);  // Total PnL initial
setTimeout(updateActivityLog, 3000);  // Activity Log initial'''
    )

# Sauvegarder
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Dashboard corrigé final:')
print('   - updateActivityLog() ajoutée')
print('   - Appels dans periodicRefresh')
print('   - Chargement initial après 2-3s')
print('')
print('🔄 Rechargez le dashboard (Ctrl+Shift+R)')
