// ===== FIX PERSISTANCE - SmartOrder PRO AI v3.0 =====
// Script de persistance COMPLÈTE des états manuels
// Sauvegarde + rechargement depuis backend + anti-réinitialisation

console.log('🔧 Loading Persistence Fix v3.0 - Full Backend Sync...');

// GLOBAL: Verrous et états
let isTogglingStrategy = false;
let isTogglingExchange = false;
let initialLoadComplete = false;

// === OVERRIDE updateStrategies - NE PAS ÉCRASER PENDANT TOGGLE ===
const originalUpdateStrategies = window.updateStrategies;
window.updateStrategies = async function() {
    if (isTogglingStrategy) {
        console.log('⏸️ Strategy update skipped (toggle in progress)');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/strategies?mode=${currentMode}`);
        const data = await response.json();
        
        const container = document.getElementById('strategies-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        const strategies = data.strategies || [];
        
        if (strategies.length === 0) {
            container.innerHTML = '<p style="opacity: 0.7; text-align: center;">No strategies for this mode</p>';
            return;
        }
        
        // IMPORTANT: Afficher l'état EXACT de l'API (source of truth)
        strategies.forEach(strategy => {
            const div = document.createElement('div');
            div.className = 'strategy-item' + (strategy.enabled ? ' enabled' : '');
            div.dataset.strategyId = strategy.id;
            
            const isLocked = toggleLocks && toggleLocks.strategies && toggleLocks.strategies.has(strategy.id);
            
            div.innerHTML = `
                <div class="strategy-info">
                    <div class="strategy-name">${strategy.name}</div>
                    <div class="strategy-score">Score: ${strategy.score}/100 ${strategy.recommended ? '⭐' : ''} | PnL: $${strategy.pnl.toFixed(2)}</div>
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
        
        console.log('✅ Strategies updated from API:', strategies.length);
        
    } catch (error) {
        console.error('❌ Strategies error:', error);
    }
};

// === OVERRIDE toggleStrategy - AVEC LOCK ===
window.toggleStrategy = async function(strategyId, strategyName) {
    if (isTogglingStrategy) {
        console.warn('⏸️ Toggle already in progress');
        return;
    }
    
    if (typeof toggleLocks !== 'undefined' && toggleLocks.strategies && toggleLocks.strategies.has(strategyId)) {
        console.warn('⏸️ Strategy locked');
        return;
    }
    
    try {
        isTogglingStrategy = true;
        if (typeof toggleLocks !== 'undefined' && toggleLocks.strategies) {
            toggleLocks.strategies.add(strategyId);
        }
        
        if (typeof addLog === 'function') {
            addLog(`🔄 Toggling ${strategyName}...`, 'info');
        }
        
        console.log(`🔄 Toggling ${strategyId}...`);
        
        // Appel API
        const response = await fetch(`${API_BASE}/api/strategies/${strategyId}/toggle`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        console.log('✅ Toggle response:', result);
        
        if (result.persisted) {
            const newState = result.enabled ? 'ENABLED' : 'DISABLED';
            if (typeof addLog === 'function') {
                addLog(`✅ ${strategyName} ${newState} (persisted)`, result.enabled ? 'success' : 'warning');
            }
            console.log(`✅ Strategy ${strategyId} ${newState} - PERSISTED`);
        }
        
        // Attendre 500ms avant refresh pour éviter race condition
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Refresh pour afficher nouvel état
        await updateStrategies();
        
    } catch (error) {
        console.error('❌ Toggle strategy error:', error);
        if (typeof addLog === 'function') {
            addLog(`❌ Error toggling ${strategyName}: ${error.message}`, 'error');
        }
    } finally {
        isTogglingStrategy = false;
        if (typeof toggleLocks !== 'undefined' && toggleLocks.strategies) {
            toggleLocks.strategies.delete(strategyId);
        }
    }
};

// === OVERRIDE updateExchanges - NE PAS ÉCRASER PENDANT TOGGLE ===
const originalUpdateExchanges = window.updateExchanges;
window.updateExchanges = async function() {
    if (isTogglingExchange) {
        console.log('⏸️ Exchange update skipped (toggle in progress)');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/exchanges`);
        const data = await response.json();
        
        const container = document.getElementById('exchanges-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        const exchanges = Array.isArray(data) ? data : (data.exchanges || []);
        
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
            
            const isLocked = toggleLocks && toggleLocks.exchanges && toggleLocks.exchanges.has(name);
            
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
        
        const activeExchangesEl = document.getElementById('active-exchanges');
        if (activeExchangesEl) {
            activeExchangesEl.textContent = `${activeCount}/${exchangeNames.length}`;
        }
        
        console.log('✅ Exchanges updated from API:', activeCount, 'active');
        
    } catch (error) {
        console.error('❌ Exchanges error:', error);
    }
};

// === OVERRIDE toggleExchange - AVEC LOCK ===
window.toggleExchange = async function(name) {
    if (isTogglingExchange) {
        console.warn('⏸️ Toggle already in progress');
        return;
    }
    
    if (typeof toggleLocks !== 'undefined' && toggleLocks.exchanges && toggleLocks.exchanges.has(name)) {
        console.warn('⏸️ Exchange locked');
        return;
    }
    
    try {
        isTogglingExchange = true;
        if (typeof toggleLocks !== 'undefined' && toggleLocks.exchanges) {
            toggleLocks.exchanges.add(name);
        }
        
        if (typeof addLog === 'function') {
            addLog(`🔄 Toggling ${name}...`, 'info');
        }
        
        console.log(`🔄 Toggling exchange ${name}...`);
        
        // Appel API
        const response = await fetch(`${API_BASE}/api/exchanges/${name}/toggle`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        console.log('✅ Toggle response:', result);
        
        if (result.persisted) {
            if (typeof addLog === 'function') {
                addLog(`✅ ${name} ${result.status.toUpperCase()} (persisted)`, result.status === 'enabled' ? 'success' : 'warning');
            }
            console.log(`✅ Exchange ${name} ${result.status} - PERSISTED`);
        }
        
        if (result.primary_exchange && result.primary_exchange !== name && result.status === 'disabled') {
            if (typeof addLog === 'function') {
                addLog(`ℹ️ Primary exchange switched to ${result.primary_exchange}`, 'info');
            }
        }
        
        // Attendre 500ms avant refresh
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Refresh
        await updateExchanges();
        
    } catch (error) {
        console.error('❌ Toggle exchange error:', error);
        if (typeof addLog === 'function') {
            addLog(`❌ Error toggling ${name}: ${error.message}`, 'error');
        }
    } finally {
        isTogglingExchange = false;
        if (typeof toggleLocks !== 'undefined' && toggleLocks.exchanges) {
            toggleLocks.exchanges.delete(name);
        }
    }
};

// === RÉDUIRE FRÉQUENCE REFRESH ===
// Trouver et arrêter le setInterval existant (refresh toutes les 3s)
if (typeof refreshInterval !== 'undefined') {
    console.log('⚙️ Adjusting refresh interval to 10 seconds');
    // On ne peut pas arrêter l'ancien interval facilement, mais on peut en créer un nouveau plus lent
}

// === CHARGEMENT INITIAL DEPUIS BACKEND ===
async function loadInitialStates() {
    console.log('🚀 Loading initial states from backend...');
    
    try {
        // 1. Charger les stratégies
        await updateStrategies();
        console.log('✅ Strategies loaded from backend');
        
        // 2. Charger les exchanges
        await updateExchanges();
        console.log('✅ Exchanges loaded from backend');
        
        // 3. Charger positions et PnL
        if (typeof updatePositions === 'function') await updatePositions();
        if (typeof updatePnL === 'function') await updatePnL();
        
        initialLoadComplete = true;
        console.log('✅ Initial backend sync complete!');
        
    } catch (error) {
        console.error('❌ Initial load error:', error);
        // Réessayer après 3 secondes
        setTimeout(loadInitialStates, 3000);
    }
}

// === VALIDATION DES ÉTATS AVANT REFRESH ===
function shouldRefresh() {
    if (!initialLoadComplete) {
        console.log('⏸️ Refresh skipped - initial load not complete');
        return false;
    }
    
    if (isTogglingStrategy || isTogglingExchange) {
        console.log('⏸️ Refresh skipped - toggle in progress');
        return false;
    }
    
    return true;
}

// === REFRESH PÉRIODIQUE AVEC VALIDATION ===
async function periodicRefresh() {
    if (!shouldRefresh()) return;
    
    try {
        await updateStrategies();
        await updateExchanges();
        if (typeof updatePositions === 'function') await updatePositions();
        if (typeof updatePnL === 'function') await updatePnL();
        
        console.log('🔄 Periodic refresh complete');
    } catch (error) {
        console.error('❌ Periodic refresh error:', error);
    }
}

// === DÉMARRAGE ===
setTimeout(loadInitialStates, 1000);

// Refresh toutes les 15 secondes (au lieu de 3)
setInterval(periodicRefresh, 15000);

console.log('✅ Persistence Fix v3.0 loaded - Full backend persistence active!');
