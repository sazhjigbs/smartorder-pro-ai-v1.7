"""
SmartOrder PRO - Phase 10: Web Dashboard
Real-time web interface for monitoring and controlling the trading system
Features:
- Live portfolio tracking with P&L
- Trading control panel
- Performance analytics and charts
- Alert management
- Real-time WebSocket updates
- Secure authentication
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps
import json
import os
from datetime import datetime, timedelta
import hashlib
import secrets

# Import our trading modules
from smartorder_engine import SmartOrderEngine
from control_panel import TradingControlPanel
from alert_system import AlertSystem
from multi_exchange_manager import MultiExchangeManager
from hybrid_trading_system import HybridTradingSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize trading components
engine = None
control_panel = None
alert_system = None
exchange_manager = None
hybrid_system = None

# User authentication (simple, expand for production)
USERS = {
    'admin': hashlib.sha256(os.getenv('ADMIN_PASSWORD', 'admin123').encode()).hexdigest()
}

def init_trading_system():
    """Initialize all trading system components"""
    global engine, control_panel, alert_system, exchange_manager, hybrid_system
    
    config = {
        'api_key': os.getenv('BYBIT_API_KEY'),
        'api_secret': os.getenv('BYBIT_API_SECRET'),
        'testnet': os.getenv('TESTNET', 'true').lower() == 'true',
        'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID')
    }
    
    try:
        engine = SmartOrderEngine(config)
        control_panel = TradingControlPanel(engine, config)
        alert_system = AlertSystem(config)
        exchange_manager = MultiExchangeManager(config)
        hybrid_system = HybridTradingSystem(engine, config)
        
        # Connect alert system to control panel
        control_panel.alert_system = alert_system
        
        print("✅ Trading system initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing trading system: {e}")
        return False

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===========================
# AUTHENTICATION ROUTES
# ===========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username in USERS and USERS[username] == password_hash:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('login'))

# ===========================
# DASHBOARD ROUTES
# ===========================

@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/portfolio')
@login_required
def portfolio():
    """Portfolio view page"""
    return render_template('portfolio.html')

@app.route('/trading')
@login_required
def trading():
    """Trading control page"""
    return render_template('trading.html')

@app.route('/alerts')
@login_required
def alerts():
    """Alerts management page"""
    return render_template('alerts.html')

@app.route('/performance')
@login_required
def performance():
    """Performance analytics page"""
    return render_template('performance.html')

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html')

# ===========================
# API ENDPOINTS
# ===========================

@app.route('/api/status')
@login_required
def api_status():
    """Get overall system status"""
    try:
        status = control_panel.get_status() if control_panel else {}
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio')
@login_required
def api_portfolio():
    """Get portfolio data"""
    try:
        if not engine:
            return jsonify({'success': False, 'error': 'Engine not initialized'}), 500
        
        portfolio = engine.get_portfolio_summary()
        
        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/positions')
@login_required
def api_positions():
    """Get open positions"""
    try:
        if not engine:
            return jsonify({'success': False, 'error': 'Engine not initialized'}), 500
        
        positions = engine.get_open_positions()
        
        return jsonify({
            'success': True,
            'positions': positions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders')
@login_required
def api_orders():
    """Get recent orders"""
    try:
        if not engine:
            return jsonify({'success': False, 'error': 'Engine not initialized'}), 500
        
        orders = engine.get_order_history(limit=50)
        
        return jsonify({
            'success': True,
            'orders': orders,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/performance')
@login_required
def api_performance():
    """Get performance metrics"""
    try:
        if not engine:
            return jsonify({'success': False, 'error': 'Engine not initialized'}), 500
        
        performance = engine.get_performance_metrics()
        
        return jsonify({
            'success': True,
            'performance': performance,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts')
@login_required
def api_alerts():
    """Get recent alerts"""
    try:
        if not alert_system:
            return jsonify({'success': False, 'error': 'Alert system not initialized'}), 500
        
        alerts = alert_system.get_recent_alerts(limit=100)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===========================
# CONTROL ENDPOINTS
# ===========================

@app.route('/api/control/start', methods=['POST'])
@login_required
def api_start_trading():
    """Start trading"""
    try:
        if not control_panel:
            return jsonify({'success': False, 'error': 'Control panel not initialized'}), 500
        
        data = request.json or {}
        mode = data.get('mode', 'auto')
        
        result = control_panel.start_trading(mode=mode)
        
        # Emit WebSocket event
        socketio.emit('trading_status', {'status': 'started', 'mode': mode})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/stop', methods=['POST'])
@login_required
def api_stop_trading():
    """Stop trading"""
    try:
        if not control_panel:
            return jsonify({'success': False, 'error': 'Control panel not initialized'}), 500
        
        result = control_panel.stop_trading()
        
        # Emit WebSocket event
        socketio.emit('trading_status', {'status': 'stopped'})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/emergency', methods=['POST'])
@login_required
def api_emergency_stop():
    """Emergency stop - close all positions"""
    try:
        if not control_panel:
            return jsonify({'success': False, 'error': 'Control panel not initialized'}), 500
        
        result = control_panel.emergency_stop()
        
        # Emit WebSocket event
        socketio.emit('emergency_stop', {'status': 'activated', 'timestamp': datetime.now().isoformat()})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/pause', methods=['POST'])
@login_required
def api_pause_trading():
    """Pause trading"""
    try:
        if not control_panel:
            return jsonify({'success': False, 'error': 'Control panel not initialized'}), 500
        
        result = control_panel.pause_trading()
        
        socketio.emit('trading_status', {'status': 'paused'})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/resume', methods=['POST'])
@login_required
def api_resume_trading():
    """Resume trading"""
    try:
        if not control_panel:
            return jsonify({'success': False, 'error': 'Control panel not initialized'}), 500
        
        result = control_panel.resume_trading()
        
        socketio.emit('trading_status', {'status': 'resumed'})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/override', methods=['POST'])
@login_required
def api_manual_override():
    """Manual trading override"""
    try:
        if not control_panel:
            return jsonify({'success': False, 'error': 'Control panel not initialized'}), 500
        
        data = request.json
        action = data.get('action')
        params = data.get('params', {})
        
        result = control_panel.manual_override(action, params)
        
        socketio.emit('manual_action', {'action': action, 'params': params})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===========================
# WEBSOCKET EVENTS
# ===========================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"Client connected: {request.sid}")
    emit('connection', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to specific data streams"""
    channel = data.get('channel')
    print(f"Client {request.sid} subscribed to {channel}")
    emit('subscribed', {'channel': channel})

def broadcast_portfolio_update():
    """Broadcast portfolio updates to all connected clients"""
    try:
        if engine:
            portfolio = engine.get_portfolio_summary()
            socketio.emit('portfolio_update', portfolio)
    except Exception as e:
        print(f"Error broadcasting portfolio: {e}")

def broadcast_trade_notification(trade):
    """Broadcast new trade notifications"""
    socketio.emit('new_trade', trade)

def broadcast_alert(alert):
    """Broadcast new alert"""
    socketio.emit('new_alert', alert)

# ===========================
# BACKGROUND TASKS
# ===========================

def start_background_tasks():
    """Start background tasks for real-time updates"""
    import threading
    import time
    
    def update_loop():
        """Background loop for broadcasting updates"""
        while True:
            try:
                broadcast_portfolio_update()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                print(f"Error in update loop: {e}")
                time.sleep(5)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()

# ===========================
# MAIN
# ===========================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SmartOrder PRO - Web Dashboard")
    print("="*60)
    
    # Initialize trading system
    if init_trading_system():
        print("\n✅ Trading system ready")
    else:
        print("\n⚠️  Trading system initialization failed - dashboard will run in limited mode")
    
    # Start background tasks
    start_background_tasks()
    
    # Run Flask app
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"\n🌐 Dashboard running at http://{host}:{port}")
    print(f"📊 Login with username: admin | password: {os.getenv('ADMIN_PASSWORD', 'admin123')}")
    print("\n" + "="*60 + "\n")
    
    socketio.run(app, host=host, port=port, debug=debug)
