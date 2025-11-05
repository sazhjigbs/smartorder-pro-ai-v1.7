// SmartOrder PRO - Dashboard Exchange Fix
// Fix exchange toggle and display

// Map display names to API IDs
const EXCHANGE_MAP = {
    'Bybit': 'bybit_spot',
    'Binance': 'binance_spot',
    'OKX': 'okx_spot',
    'KuCoin': 'kucoin_spot'
};

// Override toggleExchange function
window.toggleExchange = async function(displayName) {
    const exchangeId = EXCHANGE_MAP[displayName] || displayName.toLowerCase().replace(' ', '_');
    
    try {
        addLog(`🔄 Toggling ${displayName}...`, 'info');
        
        const response = await fetch(`${API_BASE}/api/exchanges/${exchangeId}/toggle`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        addLog(`✅ ${displayName} ${data.enabled ? 'enabled' : 'disabled'}`, 'success');
        
        // Refresh exchanges display
        await updateExchanges();
    } catch (error) {
        addLog(`❌ Error toggling ${displayName}: ${error.message}`, 'error');
    }
};

// Override updateExchanges to show correct status
const originalUpdateExchanges = window.updateExchanges;
window.updateExchanges = async function() {
    try {
        const response = await fetch(`${API_BASE}/api/exchanges`);
        const exchanges = await response.json();
        
        // Update display for each exchange
        exchanges.forEach(ex => {
            const displayName = ex.name.split(' ')[0]; // "Bybit Spot" -> "Bybit"
            const card = document.querySelector(`.exchange-card[data-exchange="${displayName}"]`);
            if (card) {
                const statusEl = card.querySelector('.exchange-status');
                if (statusEl) {
                    statusEl.textContent = ex.enabled ? '🟢 Online' : '🔴 Offline';
                    statusEl.className = `exchange-status ${ex.enabled ? 'online' : 'offline'}`;
                }
            }
        });
        
        // Update active exchanges count
        const activeCount = exchanges.filter(e => e.enabled).length;
        document.getElementById('active-exchanges').textContent = `${activeCount}/${exchanges.length}`;
        
    } catch (error) {
        console.error('Error updating exchanges:', error);
    }
};

console.log('✅ Dashboard Exchange Fix loaded');
