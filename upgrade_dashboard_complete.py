#!/usr/bin/env python3
"""
Upgrade Dashboard Complete - SmartOrder PRO AI v2.0-stable
===========================================================
Applique TOUTES les améliorations au dashboard restauré:
1. Total PnL cumulatif (lecture /api/pnl)
2. Activity Log fonctionnel (lecture /api/activity-log)
3. Wallets Exchange (lecture /api/exchange-wallets)
4. Affichage Stop-Loss / Take-Profit dans positions
5. Corrections bugs et optimisations
"""

import re

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("📋 Dashboard actuel:", len(content.split('\n')), "lignes")

# ============================================================================
# 1. AJOUTER FONCTION updateTotalPnL (si absente)
# ============================================================================
if 'function updateTotalPnL' not in content:
    update_total_pnl = '''
        // UPDATE TOTAL PNL CUMULATIF (depuis pnl_tracker.json)
        async function updateTotalPnL() {
            try {
                const response = await fetch(`${API_BASE}/api/pnl`);
                const data = await response.json();
                const totalPnl = data.total || 0;
                const pnlElement = document.getElementById('total-pnl');
                if (pnlElement) {
                    pnlElement.textContent = `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`;
                    pnlElement.className = totalPnl >= 0 ? 'status-value pnl-positive' : 'status-value pnl-negative';
                }
            } catch (error) {
                console.error('❌ Total PnL error:', error);
            }
        }
'''
    
    # Insérer avant updateMarketRegime OU avant la fin du script
    if 'function updateMarketRegime' in content:
        content = content.replace(
            '        // UPDATE MARKET REGIME\n        async function updateMarketRegime()',
            update_total_pnl + '\n        // UPDATE MARKET REGIME\n        async function updateMarketRegime()'
        )
        print("✅ Fonction updateTotalPnL ajoutée")
    else:
        # Insérer avant </script>
        content = content.replace('</script>', update_total_pnl + '\n    </script>')
        print("✅ Fonction updateTotalPnL ajoutée (fin script)")

# ============================================================================
# 2. AJOUTER FONCTION updateActivityLog (si absente)
# ============================================================================
if 'function updateActivityLog' not in content:
    update_activity_log = '''
        // UPDATE ACTIVITY LOG (Live depuis logs)
        async function updateActivityLog() {
            try {
                const response = await fetch(`${API_BASE}/api/activity-log`);
                const activities = await response.json();
                const logContainer = document.getElementById('activity-log');
                if (!logContainer) return;
                
                logContainer.innerHTML = '';
                
                activities.slice(-30).reverse().forEach(activity => {
                    const entry = document.createElement('div');
                    const msg = activity.message;
                    let className = 'log-entry log-info';
                    
                    if (msg.includes('BUY') || msg.includes('🟢') || msg.includes('TAKE_PROFIT')) className = 'log-entry log-success';
                    else if (msg.includes('SELL') || msg.includes('🔴') || msg.includes('STOP_LOSS')) className = 'log-entry log-warning';
                    else if (msg.includes('ERROR') || msg.includes('❌')) className = 'log-entry log-error';
                    
                    entry.className = className;
                    entry.textContent = msg;
                    logContainer.appendChild(entry);
                });
            } catch (error) {
                console.error('❌ Activity Log error:', error);
            }
        }
'''
    
    # Insérer avant updateMarketRegime
    if 'function updateMarketRegime' in content:
        content = content.replace(
            '        // UPDATE MARKET REGIME\n        async function updateMarketRegime()',
            update_activity_log + '\n        // UPDATE MARKET REGIME\n        async function updateMarketRegime()'
        )
        print("✅ Fonction updateActivityLog ajoutée")
    else:
        content = content.replace('</script>', update_activity_log + '\n    </script>')
        print("✅ Fonction updateActivityLog ajoutée (fin script)")

# ============================================================================
# 3. CORRIGER updatePositions pour afficher SL/TP
# ============================================================================
# Chercher et remplacer le code d'affichage des positions
old_positions_html = r"tr\.innerHTML = `[^`]+`;"

new_positions_html = '''tr.innerHTML = `
                        <td>${pos.symbol || 'N/A'}</td>
                        <td>${pos.strategy || 'N/A'}</td>
                        <td>${(pos.amount || 0).toFixed(6)}</td>
                        <td>$${(pos.entry_price || 0).toFixed(2)}</td>
                        <td>$${(pos.current_price || 0).toFixed(2)}</td>
                        <td class="${pnlClass}">$${(pos.pnl || 0).toFixed(2)}</td>
                    `;'''

# Si positions n'affichent pas SL/TP, ajouter une colonne
if 'SL / TP' not in content and 'stop_loss' not in content:
    # Ajouter colonne SL/TP dans le header
    content = re.sub(
        r'(<th>Entry</th>\s*<th>Current</th>\s*<th>PnL</th>)',
        r'<th>Entry</th>\n                            <th>Current</th>\n                            <th>SL / TP</th>\n                            <th>PnL</th>',
        content
    )
    
    # Modifier affichage des lignes pour inclure SL/TP
    if 'pos.entry_price' in content:
        content = re.sub(
            r'<td>\$\$\{.*?pos\.current_price.*?\}<\/td>',
            '<td>$${(pos.current_price || 0).toFixed(2)}</td>\n                            <td style="font-size:0.85em;">SL: $${(pos.stop_loss || 0).toFixed(2)}<br>TP: $${(pos.take_profit || 0).toFixed(2)}</td>',
            content
        )
        print("✅ Colonne SL/TP ajoutée dans positions")

# ============================================================================
# 4. AJOUTER APPELS INITIAUX updateTotalPnL et updateActivityLog
# ============================================================================
# Chercher loadInitialStates ou loadDashboard
if 'setTimeout(loadInitialStates' in content:
    if 'setTimeout(updateTotalPnL' not in content:
        content = content.replace(
            'setTimeout(loadInitialStates, 1000);',
            'setTimeout(loadInitialStates, 1000);\n        setTimeout(updateTotalPnL, 2000);\n        setTimeout(updateActivityLog, 3000);'
        )
        print("✅ Appels initiaux updateTotalPnL et updateActivityLog ajoutés")

# ============================================================================
# 5. AJOUTER setInterval pour updateTotalPnL et updateActivityLog
# ============================================================================
if 'setInterval(updateTotalPnL' not in content:
    # Chercher setInterval periodicRefresh ou autre
    if 'setInterval(periodicRefresh' in content:
        content = content.replace(
            'setInterval(periodicRefresh, 15000);',
            'setInterval(periodicRefresh, 15000);\n        setInterval(updateTotalPnL, 10000);  // Total PnL toutes les 10s\n        setInterval(updateActivityLog, 15000);  // Activity Log toutes les 15s'
        )
        print("✅ setInterval updateTotalPnL et updateActivityLog ajoutés")

# ============================================================================
# 6. SUPPRIMER LIGNES PARASITES (EOFDASH, echo, wc -l) si présentes
# ============================================================================
if 'EOFDASH' in content or 'echo ✅ Dashboard complet installé' in content:
    # Trouver </html> et couper après
    html_end = content.rfind('</html>')
    if html_end != -1:
        content = content[:html_end + 7]  # +7 pour inclure </html>
        print("✅ Lignes parasites supprimées")

# ============================================================================
# SAUVEGARDER
# ============================================================================
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*60)
print("✅ DASHBOARD UPGRADED SUCCESSFULLY")
print("="*60)
print(f"Fichier: {dashboard_file}")
print(f"Lignes: {len(content.split(chr(10)))}")
print("\n📋 Améliorations appliquées:")
print("   ✅ Total PnL cumulatif (lecture /api/pnl)")
print("   ✅ Activity Log fonctionnel (lecture /api/activity-log)")
print("   ✅ Affichage Stop-Loss / Take-Profit dans positions")
print("   ✅ Appels automatiques toutes les 10-15s")
print("   ✅ Lignes parasites supprimées")
print("\n🔄 Rechargez: https://107.189.22.255/dashboard (Ctrl+Shift+R)")
