// SmartOrder PRO AI - Dashboard Complete Fix v2.2
// Full synchronization Dashboard ↔ Backend

console.log('🔧 Loading Dashboard Complete Fix...');

const API_BASE = window.location.origin;

// ========================================
// 1. POSITIONS - AFFICHAGE RÉEL
// ========================================
async function updatePositionsReal() {
    try {
        const response = await fetch(`${API_BASE}/api/positions`);
        const positions = await response.json();
        
        const tbody = document.querySelector('#positions-table tbody');
        if (!tbody) return;
        
        if (!positions || positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">No open positions</td></tr>';
            return;
        }
        
        tbody.innerHTML = positions.map(pos => {
            const pnl = calculatePnL(pos); // À calculer depuis prix actuel
            const pnlClass = pnl >= 0 ? 'profit' : 'loss';
            return `
                <tr>
                    <td>${pos.symbol}</td>
                    <td>${pos.strategy || 'RSI_MACD_BB'}</td>
                    <td>${pos.quantity.toFixed(6)}</td>
                    <td>$${pos.entry_price.toLocaleString()}</td>
                    <td>$${pos.entry_price.toLocaleString()}</td>
                    <td>${pos.sl.toLocaleString()} / ${pos.tp.toLocaleString()}</td>
                    <td class="${pnlClass}">$${pnl.toFixed(2)}</td>
                </tr>
            `;
        }).join('');
        
        console.log(`✅ ${positions.length} positions affichées`);
    } catch (error) {
        console.error('Error updating positions:', error);
    }
}

function calculatePnL(position) {
    // PnL simplifié (à améliorer avec prix actuel)
    return 0;
}

// ========================================
// 2. EXCHANGES - AFFICHAGE ONLINE/OFFLINE
// ========================================
const EXCHANGE_MAP = {
    'Bybit': 'bybit_spot',
    'Binance': 'binance_spot',
    'OKX': 'okx_spot',
    'KuCoin': 'kucoin_spot'
};

async function updateExchangesReal() {
    try {
        const response = await fetch(`${API_BASE}/api/exchanges`);
        const exchanges = await response.json();
        
        // Map par ID pour lookup rapide
        const exchangeById = {};
        exchanges.forEach(ex => {
            exchangeById[ex.id] = ex;
        });
        
        // Update chaque exchange card
        Object.keys(EXCHANGE_MAP).forEach(displayName => {
            const apiId = EXCHANGE_MAP[displayName];
            const exchange = exchangeById[apiId];
            
            const card = document.querySelector(`.exchange-card:has(.exchange-name:contains("${displayName}"))`);
            if (card) {
                const statusEl = card.querySelector('.exchange-status');
                if (statusEl && exchange) {
                    statusEl.textContent = exchange.enabled ? '🟢 Online' : '🔴 Offline';
                    statusEl.className = `exchange-status ${exchange.enabled ? 'online' : 'offline'}`;
                }
            }
        });
        
        // Update compteur
        const activeCount = exchanges.filter(e => e.enabled).length;
        const totalCount = exchanges.length;
        const counterEl = document.getElementById('active-exchanges');
        if (counterEl) {
            counterEl.textContent = `${activeCount}/${totalCount}`;
        }
        
        console.log(`✅ Exchanges: ${activeCount}/${totalCount} online`);
    } catch (error) {
        console.error('Error updating exchanges:', error);
    }
}

// Override toggleExchange
window.toggleExchange = async function(displayName) {
    const exchangeId = EXCHANGE_MAP[displayName] || displayName.toLowerCase().replace(' ', '_');
    
    try {
        const response = await fetch(`${API_BASE}/api/exchanges/${exchangeId}/toggle`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`✅ ${displayName} ${data.enabled ? 'enabled' : 'disabled'}`);
        
        // Refresh immédiat
        await updateExchangesReal();
    } catch (error) {
        console.error(`❌ Error toggling ${displayName}:`, error);
    }
};

// ========================================
// 3. STRATÉGIES - FILTRAGE PAR MODE
// ========================================
let currentMode = 'SPOT';

async function updateStrategiesFiltered(mode) {
    try {
        const modeParam = (mode || currentMode).toLowerCase();
        const response = await fetch(`${API_BASE}/api/strategies?mode=${modeParam}`);
        const data = await response.json();
        
        const container = document.querySelector('.strategies-grid');
        if (!container) return;
        
        if (!data.strategies || data.strategies.length === 0) {
            container.innerHTML = '<p>No strategies for this mode</p>';
            return;
        }
        
        container.innerHTML = data.strategies.map(strat => `
            <div class="strategy-card ${strat.enabled ? 'enabled' : 'disabled'}">
                <div class="strategy-header">
                    <h4>${strat.name}</h4>
                    <span class="score">Score: ${strat.score}/100</span>
                </div>
                <div class="strategy-pnl">PnL: $${strat.pnl.toFixed(2)}</div>
                <button onclick="toggleStrategy('${strat.id}')" class="toggle-btn">
                    ${strat.enabled ? '✓ ENABLED' : '✗ DISABLED'}
                </button>
            </div>
        `).join('');
        
        console.log(`✅ ${data.strategies.length} stratégies ${modeParam} affichées`);
    } catch (error) {
        console.error('Error updating strategies:', error);
    }
}

// Override selectMode
window.selectMode = async function(mode) {
    currentMode = mode.toUpperCase();
    
    // Update UI active mode
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.mode-btn[data-mode="${mode}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Update mode display
    const modeDisplay = document.getElementById('mode-display');
    if (modeDisplay) {
        modeDisplay.textContent = mode;
    }
    
    // Update strategies
    await updateStrategiesFiltered(mode);
    
    // Persist mode to API
    try {
        await fetch(`${API_BASE}/api/mode`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode: mode.toLowerCase()})
        });
    } catch (error) {
        console.error('Error persisting mode:', error);
    }
};

// ========================================
// 4. WALLET - MISE À JOUR RÉELLE
// ========================================
async function updateWalletReal() {
    try {
        const response = await fetch(`${API_BASE}/api/wallet`);
        const wallet = await response.json();
        
        const balanceEl = document.getElementById('wallet-balance');
        if (balanceEl) {
            balanceEl.textContent = `$${wallet.balance_usdt.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }
        
        const pnlEl = document.getElementById('total-pnl');
        if (pnlEl) {
            pnlEl.textContent = `+$${wallet.total_pnl.toFixed(2)}`;
        }
        
        console.log(`✅ Wallet: $${wallet.balance_usdt.toFixed(2)} | PnL: $${wallet.total_pnl.toFixed(2)}`);
    } catch (error) {
        console.error('Error updating wallet:', error);
    }
}

// ========================================
// 5. AUTO-REFRESH TIMER
// ========================================
let refreshInterval = null;

function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Refresh initial
    updatePositionsReal();
    updateExchangesReal();
    updateWalletReal();
    updateStrategiesFiltered(currentMode);
    
    // Refresh toutes les 3 secondes
    refreshInterval = setInterval(() => {
        updatePositionsReal();
        updateExchangesReal();
        updateWalletReal();
    }, 3000);
    
    console.log('✅ Auto-refresh activé (3s)');
}

// ========================================
// 6. INIT AU CHARGEMENT
// ========================================
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startAutoRefresh);
} else {
    startAutoRefresh();
}

console.log('✅ Dashboard Complete Fix loaded');
