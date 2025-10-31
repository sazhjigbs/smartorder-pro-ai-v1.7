// ===== PATCH DASHBOARD SMARTORDER PRO AI - CORRECTION TOGGLES =====
// À insérer dans /opt/smartorder-pro/web/dashboard.html

// GLOBAL STATE TRACKING
let toggleLocks = {
    strategies: new Set(),
    exchanges: new Set()
};

// UPDATE STRATEGIES - AVEC TOGGLE INTERACTIF
async function updateStrategies() {
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
}

// TOGGLE STRATEGY - AVEC API + PERSISTANCE + STATE LOCKING
async function toggleStrategy(strategyId, strategyName) {
    // Vérifier lock
    if (toggleLocks.strategies.has(strategyId)) {
        addLog(`⏳ ${strategyName} is already being toggled...`, 'info');
        return;
    }
    
    try {
        // Lock UI
        toggleLocks.strategies.add(strategyId);
        addLog(`🔄 Toggling ${strategyName}...`, 'info');
        
        // Refresh UI to show loader
        await updateStrategies();
        
        // Appel API
        const response = await fetch(`${API_BASE}/api/strategies/${strategyId}/toggle`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Log succès
        const newState = result.enabled ? 'ENABLED' : 'DISABLED';
        addLog(`✅ ${strategyName} ${newState}`, result.enabled ? 'success' : 'warning');
        
        // Refresh pour afficher nouvel état depuis backend (source of truth)
        await updateStrategies();
        
    } catch (error) {
        console.error('Toggle strategy error:', error);
        addLog(`❌ Error toggling ${strategyName}: ${error.message}`, 'error');
        
        // Refresh pour revenir à l'état réel
        await updateStrategies();
        
    } finally {
        // Unlock UI
        toggleLocks.strategies.delete(strategyId);
    }
}

// UPDATE EXCHANGES - AVEC TOGGLE INTERACTIF
async function updateExchanges() {
    try {
        const response = await fetch(`${API_BASE}/api/exchanges`);
        const data = await response.json();
        
        const container = document.getElementById('exchanges-container');
        container.innerHTML = '';
        
        const exchanges = Array.isArray(data) ? data : (data.exchanges || []);
        
        // S'assurer que KuCoin est présent
        const exchangeNames = ['Bybit', 'Binance', 'OKX', 'KuCoin'];
        const exchangesMap = {};
        
        exchanges.forEach(ex => {
            exchangesMap[ex.name] = ex;
        });
        
        let activeCount = 0;
        exchangeNames.forEach(name => {
            const exchange = exchangesMap[name] || {name, connected: false};
            const connected = exchange.connected !== false;
            const isPrimary = exchange.primary === true;
            if (connected) activeCount++;
            
            const isLocked = toggleLocks.exchanges.has(name);
            
            const div = document.createElement('div');
            div.className = 'exchange-item';
            
            div.innerHTML = `
                <div>
                    <div style="font-weight: bold; font-size: 1.1em;">
                        ${name} ${isPrimary ? '⭐ PRIMARY' : ''}
                    </div>
                    <div style="font-size: 0.9em; opacity: 0.8; margin-top: 5px;">
                        ${connected ? '🟢 Connected' : '🔴 Offline'}
                        ${isLocked ? ' ⏳ Processing...' : ''}
                    </div>
                </div>
                <div class="exchange-toggle ${connected ? 'active' : ''} ${isLocked ? 'locked' : ''}" 
                     onclick="${isLocked ? '' : `toggleExchange('${name}')`}">
                </div>
            `;
            
            container.appendChild(div);
        });
        
        document.getElementById('active-exchanges').textContent = `${activeCount}/${exchangeNames.length}`;
        
    } catch (error) {
        console.error('Exchanges error:', error);
        addLog('❌ Error loading exchanges', 'error');
    }
}

// TOGGLE EXCHANGE - AVEC API + PERSISTANCE + STATE LOCKING
async function toggleExchange(name) {
    // Vérifier lock
    if (toggleLocks.exchanges.has(name)) {
        addLog(`⏳ ${name} is already being toggled...`, 'info');
        return;
    }
    
    try {
        // Lock UI
        toggleLocks.exchanges.add(name);
        addLog(`🔄 Toggling ${name}...`, 'info');
        
        // Refresh UI to show loader
        await updateExchanges();
        
        // Appel API
        const response = await fetch(`${API_BASE}/api/exchanges/${name}/toggle`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Log succès
        addLog(`✅ ${name} ${result.status.toUpperCase()}`, result.status === 'enabled' ? 'success' : 'warning');
        
        if (result.primary_exchange && result.primary_exchange !== name && result.status === 'disabled') {
            addLog(`ℹ️ Primary exchange switched to ${result.primary_exchange}`, 'info');
        }
        
        // Refresh pour afficher nouvel état depuis backend
        await updateExchanges();
        
    } catch (error) {
        console.error('Toggle exchange error:', error);
        addLog(`❌ Error toggling ${name}: ${error.message}`, 'error');
        
        // Refresh pour revenir à l'état réel
        await updateExchanges();
        
    } finally {
        // Unlock UI
        toggleLocks.exchanges.delete(name);
    }
}

// SELECT PRIMARY EXCHANGE
async function selectPrimaryExchange(exchangeName) {
    try {
        addLog(`🎯 Setting ${exchangeName} as primary exchange...`, 'info');
        
        const response = await fetch(`${API_BASE}/api/exchanges/select`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({exchange: exchangeName})
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const result = await response.json();
        addLog(`✅ ${exchangeName} is now PRIMARY exchange`, 'success');
        
        await updateExchanges();
        
    } catch (error) {
        console.error('Select primary exchange error:', error);
        addLog(`❌ Error selecting primary exchange: ${error.message}`, 'error');
    }
}

// STYLES CSS ADDITIONNELS
const additionalStyles = `
<style>
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
</style>
`;

console.log('✅ Dashboard Toggle Fix Loaded');
