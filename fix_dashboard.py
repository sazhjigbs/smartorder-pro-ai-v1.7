#!/usr/bin/env python3
"""
Correction automatique du dashboard SmartOrder PRO
- Ajoute l'appel API pour les exchanges
- Ajoute l'appel API pour les funding rates
- Ajoute les containers manquants
"""

import re

# Lire le dashboard actuel
with open('/opt/smartorder-pro/web/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("🔧 Correction automatique du Dashboard...")
print()

# Backup
with open('/opt/smartorder-pro/web/dashboard.html.backup_auto', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Backup créé: dashboard.html.backup_auto")

# ============================================================================
# 1. Ajouter la fonction updateExchanges()
# ============================================================================
exchanges_function = """
        // UPDATE EXCHANGES
        async function updateExchanges() {
            try {
                const response = await fetch(`${API_BASE}/api/exchanges`);
                const data = await response.json();
                
                const container = document.getElementById('exchanges-status');
                if (!container) return;
                
                container.innerHTML = '';
                
                const exchanges = Array.isArray(data) ? data : (data.exchanges || []);
                
                if (exchanges.length === 0) {
                    container.innerHTML = '<p style="opacity: 0.7; text-align: center;">No exchanges connected</p>';
                    return;
                }
                
                exchanges.forEach(exchange => {
                    const div = document.createElement('div');
                    div.className = 'exchange-item';
                    div.style.cssText = 'background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin: 10px 0;';
                    
                    const connected = exchange.connected !== false;
                    const statusColor = connected ? '#10b981' : '#ef4444';
                    const statusText = connected ? 'CONNECTED' : 'DISCONNECTED';
                    
                    div.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 1.2em;">${exchange.name || 'Unknown'}</strong>
                                <div style="font-size: 0.9em; opacity: 0.8; margin-top: 5px;">
                                    Balance: ${JSON.stringify(exchange.balance || {})}
                                </div>
                            </div>
                            <span style="background: ${statusColor}; padding: 8px 15px; border-radius: 20px; font-size: 0.9em; font-weight: bold;">
                                ${statusText}
                            </span>
                        </div>
                    `;
                    
                    container.appendChild(div);
                });
                
            } catch (error) {
                console.error('Exchanges update error:', error);
            }
        }

"""

# Trouver où insérer (avant updatePositions)
if 'async function updatePositions()' in content:
    content = content.replace(
        '        // UPDATE POSITIONS\n        async function updatePositions()',
        exchanges_function + '        // UPDATE POSITIONS\n        async function updatePositions()'
    )
    print("✅ Fonction updateExchanges() ajoutée")
else:
    print("⚠️  Impossible de trouver l'emplacement pour updateExchanges()")

# ============================================================================
# 2. Ajouter la fonction updateFundingRates()
# ============================================================================
funding_function = """
        // UPDATE FUNDING RATES
        async function updateFundingRates() {
            try {
                const response = await fetch(`${API_BASE}/api/funding-rates`);
                const data = await response.json();
                
                const container = document.getElementById('funding-rates');
                if (!container) return;
                
                container.innerHTML = '';
                
                const rates = data.funding_rates || data || [];
                
                if (rates.length === 0) {
                    container.innerHTML = '<p style="opacity: 0.7; text-align: center;">No funding rates available</p>';
                    return;
                }
                
                rates.forEach(rate => {
                    const div = document.createElement('div');
                    div.className = 'funding-rate';
                    
                    const rateValue = rate.rate || rate.funding_rate || 0;
                    const rateClass = rateValue >= 0 ? 'funding-positive' : 'funding-negative';
                    const rateSymbol = rateValue >= 0 ? '+' : '';
                    
                    div.innerHTML = `
                        <strong>${rate.symbol || rate.pair || 'Unknown'}</strong>
                        <span class="${rateClass}">${rateSymbol}${(rateValue * 100).toFixed(4)}%</span>
                    `;
                    
                    container.appendChild(div);
                });
                
            } catch (error) {
                console.error('Funding rates update error:', error);
                const container = document.getElementById('funding-rates');
                if (container) {
                    container.innerHTML = '<p style="opacity: 0.7; text-align: center; color: #ef4444;">Error loading funding rates</p>';
                }
            }
        }

"""

# Insérer après updateExchanges
if 'async function updatePositions()' in content:
    content = content.replace(
        exchanges_function + '        // UPDATE POSITIONS\n        async function updatePositions()',
        exchanges_function + funding_function + '        // UPDATE POSITIONS\n        async function updatePositions()'
    )
    print("✅ Fonction updateFundingRates() ajoutée")
else:
    print("⚠️  Impossible de trouver l'emplacement pour updateFundingRates()")

# ============================================================================
# 3. Ajouter les appels dans les intervalles
# ============================================================================

# Trouver la section setInterval pour updateStrategies
if 'setInterval(async () => {' in content and 'updateStrategies()' in content:
    # Ajouter les nouveaux appels
    old_interval = 'setInterval(async () => {\n            await updateStrategies();\n            await updatePositions();'
    new_interval = '''setInterval(async () => {
            await updateStrategies();
            await updateExchanges();
            await updateFundingRates();
            await updatePositions();'''
    
    if old_interval in content:
        content = content.replace(old_interval, new_interval)
        print("✅ Appels updateExchanges() et updateFundingRates() ajoutés dans l'intervalle")
    else:
        print("⚠️  Pattern d'intervalle non trouvé, recherche alternative...")

# ============================================================================
# 4. Ajouter le container exchanges-status s'il manque
# ============================================================================
if 'exchanges-status' not in content:
    # Trouver où ajouter le container (après strategies)
    strategies_section = '<div id="strategies-list">'
    if strategies_section in content:
        exchanges_container = '''
        
        <div class="section">
            <h2>💱 Connected Exchanges</h2>
            <div id="exchanges-status">
                <p style="opacity: 0.7; text-align: center;">Loading exchanges...</p>
            </div>
        </div>
'''
        # Trouver la fin de la section strategies
        insert_pos = content.find('</div>\n            </div>\n\n            <div class="section">\n                <h2>📊 Open Positions</h2>')
        if insert_pos > 0:
            content = content[:insert_pos] + '            </div>\n\n            <div class="section">\n                <h2>💱 Connected Exchanges</h2>\n                <div id="exchanges-status">\n                    <p style="opacity: 0.7; text-align: center;">Loading exchanges...</p>\n                </div>' + content[insert_pos:]
            print("✅ Container exchanges-status ajouté")
        else:
            print("⚠️  Position d'insertion pour exchanges-status non trouvée")

# ============================================================================
# 5. Écrire le fichier corrigé
# ============================================================================
with open('/opt/smartorder-pro/web/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("✅ Dashboard corrigé avec succès!")
print("📝 Fichier: /opt/smartorder-pro/web/dashboard.html")
print("💾 Backup: /opt/smartorder-pro/web/dashboard.html.backup_auto")
print()
print("🔄 Rechargez https://107.189.22.255/dashboard pour voir les changements")
