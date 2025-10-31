#!/usr/bin/env python3
"""
Fix Total PnL Dashboard - SmartOrder PRO AI v2.0-stable
=======================================================
Corrige le calcul du Total PnL pour qu'il lise le fichier pnl_tracker.json
au lieu de calculer uniquement depuis les positions ouvertes.
"""

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

# Lire le fichier
with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Supprimer l'ancien calcul de totalPnl dans updatePositions
old_pnl_calculation = '''                const pnlElement = document.getElementById('total-pnl');
                pnlElement.textContent = `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`;
                pnlElement.className = totalPnl >= 0 ? 'status-value pnl-positive' : 'status-value pnl-negative';'''

content = content.replace(old_pnl_calculation, '// Total PnL moved to dedicated function updateTotalPnL()')

# 2. Ajouter nouvelle fonction updateTotalPnL après updatePositions
new_function = '''

        // UPDATE TOTAL PNL (CUMULATIF RÉEL depuis pnl_tracker.json)
        async function updateTotalPnL() {
            try {
                const response = await fetch(`${API_BASE}/api/pnl`);
                const data = await response.json();
                
                const totalPnl = data.total || 0;
                
                const pnlElement = document.getElementById('total-pnl');
                pnlElement.textContent = `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`;
                pnlElement.className = totalPnl >= 0 ? 'status-value pnl-positive' : 'status-value pnl-negative';
                
                console.log('📊 Total PnL mis à jour:', totalPnl.toFixed(2), '(cumulatif)');
                
            } catch (error) {
                console.error('❌ Erreur Total PnL:', error);
            }
        }'''

# Insérer après la fonction updatePositions (après la ligne "async function updateMarketRegime")
content = content.replace(
    '        // UPDATE MARKET REGIME\n        async function updateMarketRegime()',
    new_function + '\n\n        // UPDATE MARKET REGIME\n        async function updateMarketRegime()'
)

# 3. Ajouter l'appel à updateTotalPnL dans les setInterval
# Trouver les setInterval existants et ajouter updateTotalPnL
if 'setInterval(updatePositions' in content and 'setInterval(updateTotalPnL' not in content:
    # Ajouter après le premier setInterval
    content = content.replace(
        'setInterval(updatePositions, 5000);',
        '''setInterval(updatePositions, 5000);
        setInterval(updateTotalPnL, 10000);  // Total PnL toutes les 10s'''
    )

# 4. Ajouter l'appel initial à updateTotalPnL dans loadDashboard
if 'async function loadDashboard()' in content:
    # Chercher "await updatePositions();" et ajouter updateTotalPnL après
    content = content.replace(
        'await updatePositions();',
        '''await updatePositions();
        await updateTotalPnL();  // Charger Total PnL cumulatif'''
    )

# Sauvegarder
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Dashboard corrigé:')
print('   - Total PnL lit maintenant /api/pnl (pnl_tracker.json)')
print('   - Fonction updateTotalPnL() ajoutée')
print('   - Mise à jour automatique toutes les 10s')
print('')
print('🔄 Rechargez le dashboard dans votre navigateur pour voir le Total PnL cumulatif réel')
