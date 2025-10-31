// ===== FIX POSITIONS & PNL DISPLAY - SmartOrder PRO AI =====

// Override updatePositions pour afficher correctement les positions
window.updatePositions = async function() {
    try {
        const response = await fetch(`${API_BASE}/api/positions`);
        const positions = await response.json();
        
        const tbody = document.querySelector('#positions-list');
        if (!tbody) {
            console.warn('Element #positions-list not found');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (!positions || positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; opacity: 0.7;">No open positions</td></tr>';
            return;
        }
        
        positions.forEach(pos => {
            const pnlClass = pos.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            const pnlSign = pos.pnl >= 0 ? '+' : '';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${pos.symbol}</strong></td>
                <td>${pos.strategy}</td>
                <td>${pos.amount.toFixed(4)}</td>
                <td>$${pos.entry_price.toFixed(2)}</td>
                <td>$${pos.current_price.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}$${pos.pnl.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
        
        console.log('✅ Positions updated:', positions.length);
        
    } catch (error) {
        console.error('❌ Positions error:', error);
        if (typeof addLog === 'function') {
            addLog('❌ Error loading positions', 'error');
        }
    }
};

// Override updatePnL pour afficher correctement le PnL total
window.updatePnL = async function() {
    try {
        const response = await fetch(`${API_BASE}/api/pnl`);
        const data = await response.json();
        
        const pnlElement = document.getElementById('total-pnl');
        if (pnlElement && data.total_pnl !== undefined) {
            const pnl = data.total_pnl;
            const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            const pnlSign = pnl >= 0 ? '+' : '';
            pnlElement.className = pnlClass;
            pnlElement.textContent = `${pnlSign}$${pnl.toFixed(2)}`;
            console.log('✅ PnL updated:', pnl);
        }
        
    } catch (error) {
        console.error('❌ PnL error:', error);
    }
};

// Fonction updateAll améliorée
window.updateAll = async function() {
    try {
        await Promise.all([
            updatePositions(),
            updatePnL(),
            updateStrategies(),
            updateExchanges(),
            updateMarketRegime()
        ]);
    } catch (error) {
        console.error('Update error:', error);
    }
};

// Force refresh initial au chargement
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            console.log('🚀 Initial dashboard load...');
            updatePositions();
            updatePnL();
            updateStrategies();
            updateExchanges();
        }, 500);
    });
} else {
    // DOM déjà chargé
    setTimeout(() => {
        console.log('🚀 Initial dashboard load (immediate)...');
        updatePositions();
        updatePnL();
        updateStrategies();
        updateExchanges();
    }, 100);
}

// Refresh automatique toutes les 5 secondes
setInterval(() => {
    updatePositions();
    updatePnL();
}, 5000);

console.log('✅ Dashboard Positions & PnL Fix v2.0 loaded');
