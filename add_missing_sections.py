#!/usr/bin/env python3
"""
Add Missing Sections - Dashboard SmartOrder PRO v2.0-stable
============================================================
Ajoute PRÉCISÉMENT ce qui manque:
1. 💰 Wallet USDT dans status-bar
2. Section "Wallets Exchange" (balances par exchange)
3. Section "Stratégies AI Complètes" avec indicateurs techniques
"""

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("📋 Dashboard actuel:", len(content.split('\n')), "lignes")

# =============================================================================
# 1. AJOUTER 💰 WALLET USDT dans status-bar (après Total PnL)
# =============================================================================
if '💰' not in content and 'Wallet USDT' not in content:
    wallet_item = '''            <div class="status-item glass">
                <div class="status-label">💰 Wallet USDT</div>
                <div class="status-value" id="wallet-balance">$10,000</div>
            </div>
'''
    
    # Insérer après Total PnL
    content = content.replace(
        '            <div class="status-item glass">\n                <div class="status-label">Market Regime</div>',
        wallet_item + '            <div class="status-item glass">\n                <div class="status-label">Market Regime</div>'
    )
    print("✅ Wallet USDT ajouté dans status-bar")

# =============================================================================
# 2. AJOUTER SECTION "WALLETS EXCHANGE" (avant Open Positions)
# =============================================================================
if 'Wallets Exchange' not in content and 'id="wallets-container"' not in content:
    wallets_section = '''
        <!-- WALLETS PAR EXCHANGE -->
        <div class="dashboard-grid" style="grid-column: 1 / -1; margin-top: 20px;">
            <div class="card glass" style="grid-column: 1 / -1;">
                <h2>💰 Wallets Exchange - Balances Réelles</h2>
                <div id="wallets-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 15px;">
                    <!-- Wallets chargés dynamiquement -->
                </div>
                <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; text-align: center;">
                    <strong>Total Balance:</strong> <span id="total-balance-exchanges" style="font-size: 1.3em; color: #10b981;">$0.00</span>
                </div>
            </div>
        </div>
'''
    
    # Insérer avant Open Positions
    if '<!-- OPEN POSITIONS -->' in content:
        content = content.replace(
            '        <!-- OPEN POSITIONS -->',
            wallets_section + '\n        <!-- OPEN POSITIONS -->'
        )
        print("✅ Section Wallets Exchange ajoutée")

# =============================================================================
# 3. AJOUTER SECTION "STRATÉGIES AI COMPLÈTES" (après Open Positions)
# =============================================================================
if 'Stratégies AI - Liste Complète' not in content:
    strategies_complete_section = '''
        <!-- STRATÉGIES AI COMPLÈTES AVEC INDICATEURS -->
        <div class="dashboard-grid" style="grid-column: 1 / -1; margin-top: 20px;">
            <div class="card glass" style="grid-column: 1 / -1;">
                <h2>🧠 Stratégies AI - Liste Complète avec Indicateurs Techniques</h2>
                <div style="margin-bottom: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="filterStrategiesComplete('all')" class="btn btn-primary" style="padding: 8px 16px;">Toutes</button>
                    <button onclick="filterStrategiesComplete('spot')" class="btn btn-primary" style="padding: 8px 16px;">Spot</button>
                    <button onclick="filterStrategiesComplete('futures')" class="btn btn-primary" style="padding: 8px 16px;">Futures</button>
                    <button onclick="filterStrategiesComplete('enabled')" class="btn btn-success" style="padding: 8px 16px;">Activées</button>
                </div>
                <div id="strategies-complete-list" style="max-height: 600px; overflow-y: auto;">
                    <!-- Stratégies chargées dynamiquement -->
                </div>
            </div>
        </div>
'''
    
    # Insérer avant Market Regime Detector OU avant Emergency Controls
    if '<!-- MARKET REGIME DETECTOR -->' in content:
        content = content.replace(
            '        <!-- MARKET REGIME DETECTOR -->',
            strategies_complete_section + '\n        <!-- MARKET REGIME DETECTOR -->'
        )
        print("✅ Section Stratégies AI Complètes ajoutée")
    elif '<!-- EMERGENCY CONTROLS -->' in content:
        content = content.replace(
            '        <!-- EMERGENCY CONTROLS -->',
            strategies_complete_section + '\n        <!-- EMERGENCY CONTROLS -->'
        )
        print("✅ Section Stratégies AI Complètes ajoutée (avant Emergency)")

# =============================================================================
# 4. AJOUTER FONCTION updateWallet()
# =============================================================================
if 'function updateWallet()' not in content:
    update_wallet_func = '''
        // UPDATE WALLET BALANCE
        async function updateWallet() {
            try {
                const response = await fetch(`${API_BASE}/api/wallet`);
                const data = await response.json();
                const walletEl = document.getElementById('wallet-balance');
                if (walletEl) {
                    walletEl.textContent = `$${data.balance_usdt.toLocaleString()}`;
                }
            } catch (error) {
                console.error('❌ Wallet error:', error);
            }
        }
'''
    
    # Insérer avant updateTotalPnL
    if 'function updateTotalPnL' in content:
        content = content.replace(
            '        // UPDATE TOTAL PNL CUMULATIF',
            update_wallet_func + '\n        // UPDATE TOTAL PNL CUMULATIF'
        )
        print("✅ Fonction updateWallet() ajoutée")

# =============================================================================
# 5. AJOUTER FONCTION updateExchangeWallets()
# =============================================================================
if 'function updateExchangeWallets()' not in content:
    update_exchange_wallets_func = '''
        // UPDATE EXCHANGE WALLETS
        async function updateExchangeWallets() {
            try {
                const response = await fetch(`${API_BASE}/api/exchange-wallets`);
                const data = await response.json();
                const container = document.getElementById('wallets-container');
                if (!container) return;
                
                container.innerHTML = '';
                let totalBalance = 0;
                
                for (const [key, wallet] of Object.entries(data.wallets || {})) {
                    totalBalance += wallet.balance_usdt || 0;
                    
                    const card = document.createElement('div');
                    card.style.cssText = 'background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);';
                    
                    const statusColor = wallet.connected ? '#10b981' : '#ef4444';
                    const paperBadge = wallet.paper_trading ? '<span style="background:#f59e0b;padding:4px 8px;border-radius:6px;font-size:0.8em;">PAPER</span>' : '';
                    
                    card.innerHTML = `
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                            <strong style="font-size:1.1em;"><span style="color:${statusColor};">●</span> ${wallet.exchange}</strong>
                            ${paperBadge}
                        </div>
                        <div style="font-size:1.6em;color:#10b981;margin:10px 0;">$${(wallet.balance_usdt || 0).toLocaleString()}</div>
                        <div style="font-size:0.9em;opacity:0.8;">
                            Available: $${(wallet.available || 0).toLocaleString()}<br>
                            In Positions: $${(wallet.in_positions || 0).toLocaleString()}
                        </div>
                    `;
                    container.appendChild(card);
                }
                
                const totalEl = document.getElementById('total-balance-exchanges');
                if (totalEl) totalEl.textContent = `$${totalBalance.toLocaleString()}`;
                
                console.log('💰 Wallets updated');
            } catch (error) {
                console.error('❌ Exchange Wallets error:', error);
            }
        }
'''
    
    if 'function updateWallet' in content:
        content = content.replace(
            '        // UPDATE TOTAL PNL CUMULATIF',
            update_exchange_wallets_func + '\n        // UPDATE TOTAL PNL CUMULATIF'
        )
        print("✅ Fonction updateExchangeWallets() ajoutée")

# =============================================================================
# 6. AJOUTER FONCTION updateStrategiesComplete() et filterStrategiesComplete()
# =============================================================================
if 'function updateStrategiesComplete()' not in content:
    strategies_complete_funcs = '''
        // UPDATE STRATEGIES COMPLETE
        let strategiesCompleteCache = [];
        
        async function updateStrategiesComplete() {
            try {
                const response = await fetch(`${API_BASE}/api/strategies/complete`);
                const data = await response.json();
                strategiesCompleteCache = data.strategies || [];
                renderStrategiesComplete(strategiesCompleteCache);
                console.log('🧠 Strategies complete updated:', strategiesCompleteCache.length);
            } catch (error) {
                console.error('❌ Strategies complete error:', error);
            }
        }
        
        function renderStrategiesComplete(strategies) {
            const container = document.getElementById('strategies-complete-list');
            if (!container) return;
            
            container.innerHTML = '';
            
            strategies.forEach(strat => {
                const item = document.createElement('div');
                item.style.cssText = 'background:rgba(255,255,255,0.05);padding:15px;border-radius:10px;margin:10px 0;border-left:4px solid ' + (strat.enabled ? '#10b981' : 'transparent');
                
                const indicators = (strat.indicators || []).map(ind => 
                    `<span style="display:inline-block;background:rgba(102,126,234,0.3);padding:4px 10px;border-radius:8px;font-size:0.85em;margin:3px;border:1px solid rgba(102,126,234,0.5);">${ind}</span>`
                ).join('');
                
                item.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <div>
                            <strong style="font-size:1.1em;">${strat.name}</strong>
                            <span style="margin-left:10px;opacity:0.7;">[${(strat.mode || 'spot').toUpperCase()}]</span>
                        </div>
                        <span style="background:${strat.enabled ? '#10b981' : '#6b7280'};padding:4px 12px;border-radius:8px;font-size:0.85em;">
                            ${strat.enabled ? 'ACTIVE' : 'INACTIVE'}
                        </span>
                    </div>
                    <div style="font-size:0.9em;opacity:0.8;margin-bottom:8px;">
                        Score: ${strat.score}/100 | PnL: $${strat.pnl.toFixed(2)} | Win: ${strat.win_rate}%
                    </div>
                    <div style="margin-top:10px;">
                        <strong style="font-size:0.9em;">Indicateurs:</strong><br>
                        ${indicators}
                    </div>
                `;
                container.appendChild(item);
            });
        }
        
        function filterStrategiesComplete(filter) {
            let filtered = strategiesCompleteCache;
            if (filter === 'spot') filtered = strategiesCompleteCache.filter(s => s.mode === 'spot');
            else if (filter === 'futures') filtered = strategiesCompleteCache.filter(s => s.mode === 'futures');
            else if (filter === 'enabled') filtered = strategiesCompleteCache.filter(s => s.enabled);
            renderStrategiesComplete(filtered);
        }
'''
    
    if 'function updateWallet' in content:
        content = content.replace(
            '        // UPDATE TOTAL PNL CUMULATIF',
            strategies_complete_funcs + '\n        // UPDATE TOTAL PNL CUMULATIF'
        )
        print("✅ Fonctions Stratégies Complètes ajoutées")

# =============================================================================
# 7. AJOUTER APPELS INITIAUX ET PÉRIODIQUES
# =============================================================================
if 'setTimeout(updateWallet' not in content and 'setTimeout(updateTotalPnL, 2000)' in content:
    content = content.replace(
        'setTimeout(updateTotalPnL, 2000);',
        'setTimeout(updateWallet, 1500);\n        setTimeout(updateTotalPnL, 2000);\n        setTimeout(updateExchangeWallets, 3500);\n        setTimeout(updateStrategiesComplete, 4000);'
    )
    print("✅ Appels initiaux Wallet + Exchange Wallets + Strategies Complete ajoutés")

if 'setInterval(updateWallet' not in content and 'setInterval(updateTotalPnL, 10000)' in content:
    content = content.replace(
        'setInterval(updateActivityLog, 15000);',
        'setInterval(updateActivityLog, 15000);\n        setInterval(updateWallet, 30000);\n        setInterval(updateExchangeWallets, 30000);\n        setInterval(updateStrategiesComplete, 60000);'
    )
    print("✅ setInterval Wallet + Exchange Wallets + Strategies Complete ajoutés")

# =============================================================================
# SAUVEGARDER
# =============================================================================
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*70)
print("✅ TOUTES LES SECTIONS MANQUANTES AJOUTÉES")
print("="*70)
print(f"Fichier: {dashboard_file}")
print(f"Lignes: {len(content.split(chr(10)))}")
print("\n📋 Sections ajoutées:")
print("   ✅ 💰 Wallet USDT (status-bar)")
print("   ✅ Section Wallets Exchange (balances par exchange)")
print("   ✅ Section Stratégies AI Complètes (avec indicateurs)")
print("   ✅ Fonctions JS: updateWallet, updateExchangeWallets, updateStrategiesComplete")
print("   ✅ Filtres: Toutes/Spot/Futures/Activées")
print("\n🔄 Rechargez: https://107.189.22.255/dashboard (Ctrl+Shift+R)")
