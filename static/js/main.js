// SmartOrder PRO - Main JavaScript

// Global variables
let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('SmartOrder PRO Dashboard Initialized');
    initializeWebSocket();
    addEventListeners();
});

// WebSocket initialization
function initializeWebSocket() {
    if (!socket) {
        socket = io({
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: MAX_RECONNECT_ATTEMPTS
        });
        
        socket.on('connect', handleConnect);
        socket.on('disconnect', handleDisconnect);
        socket.on('connect_error', handleConnectError);
        socket.on('reconnect', handleReconnect);
        socket.on('reconnect_failed', handleReconnectFailed);
        
        // Custom events
        socket.on('portfolio_update', handlePortfolioUpdate);
        socket.on('new_trade', handleNewTrade);
        socket.on('new_alert', handleNewAlert);
        socket.on('trading_status', handleTradingStatus);
        socket.on('emergency_stop', handleEmergencyStop);
    }
}

// WebSocket event handlers
function handleConnect() {
    console.log('✅ Connected to server');
    reconnectAttempts = 0;
    updateConnectionStatus(true);
    showNotification('Connected to server', 'success');
}

function handleDisconnect() {
    console.log('❌ Disconnected from server');
    updateConnectionStatus(false);
    showNotification('Disconnected from server', 'warning');
}

function handleConnectError(error) {
    console.error('Connection error:', error);
    reconnectAttempts++;
    
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        showNotification('Failed to connect to server', 'danger');
    }
}

function handleReconnect(attemptNumber) {
    console.log(`Reconnected after ${attemptNumber} attempts`);
    showNotification('Reconnected to server', 'success');
}

function handleReconnectFailed() {
    console.error('❌ Reconnection failed');
    showNotification('Unable to reconnect. Please refresh the page.', 'danger');
}

function handlePortfolioUpdate(data) {
    console.log('Portfolio update received:', data);
    // This will be handled by individual pages
    if (typeof updatePortfolioData === 'function') {
        updatePortfolioData(data);
    }
}

function handleNewTrade(data) {
    console.log('New trade:', data);
    showNotification(`New ${data.side} trade: ${data.symbol} @ $${data.price}`, 'info');
    
    if (typeof addTradeToTable === 'function') {
        addTradeToTable(data);
    }
}

function handleNewAlert(data) {
    console.log('New alert:', data);
    showNotification(data.message, data.level || 'info');
    
    if (typeof addAlert === 'function') {
        addAlert(data);
    }
}

function handleTradingStatus(data) {
    console.log('Trading status update:', data);
    if (typeof updateStatus === 'function') {
        updateStatus(data);
    }
}

function handleEmergencyStop(data) {
    console.error('⚠️ EMERGENCY STOP ACTIVATED');
    showNotification('EMERGENCY STOP ACTIVATED!', 'danger', 5000);
}

// Connection status update
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-status');
    const text = document.getElementById('connection-text');
    
    if (indicator && text) {
        if (connected) {
            indicator.className = 'status-indicator status-connected';
            text.textContent = 'Connected';
        } else {
            indicator.className = 'status-indicator status-disconnected';
            text.textContent = 'Disconnected';
        }
    }
}

// Notification system
function showNotification(message, type = 'info', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        notification.remove();
    }, duration);
}

// Event listeners
function addEventListeners() {
    // Add any global event listeners here
}

// Utility functions
function formatCurrency(value, decimals = 2) {
    return '$' + value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatPercent(value, decimals = 2) {
    return value.toFixed(decimals) + '%';
}

function formatNumber(value, decimals = 2) {
    return value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

// API call wrapper
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API call failed');
        }
        
        return result;
    } catch (error) {
        console.error('API call error:', error);
        showNotification('API Error: ' + error.message, 'danger');
        throw error;
    }
}

// Export functions for use in other scripts
window.smartorder = {
    showNotification,
    formatCurrency,
    formatPercent,
    formatNumber,
    formatDate,
    formatTime,
    apiCall,
    socket: () => socket
};
