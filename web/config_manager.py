# -*- coding: utf-8 -*-
"""Web Config Manager - Strategy configuration via web interface"""
from flask import Flask, render_template_string, request, jsonify
import json
import os

app = Flask(__name__)

CONFIG_FILE = 'config/trading_config.json'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>SmartOrder PRO - Config Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: none;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            margin-right: 10px;
        }
        .btn-primary {
            background: #4ade80;
            color: #000;
        }
        .btn-secondary {
            background: #94a3b8;
            color: #000;
        }
        .btn:hover { opacity: 0.8; }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: none;
        }
        .alert-success { background: #4ade80; color: #000; }
        .alert-error { background: #f87171; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 SmartOrder PRO - Config Manager</h1>
        
        <div id="alert" class="alert"></div>
        
        <div class="card">
            <h2>Trading Configuration</h2>
            <form id="configForm">
                <div class="form-group">
                    <label>Symbol:</label>
                    <input type="text" id="symbol" name="symbol" value="BTCUSDT" required>
                </div>
                
                <div class="form-group">
                    <label>Timeframe:</label>
                    <select id="timeframe" name="timeframe">
                        <option value="1m">1 Minute</option>
                        <option value="5m" selected>5 Minutes</option>
                        <option value="15m">15 Minutes</option>
                        <option value="1h">1 Hour</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Strategy:</label>
                    <select id="strategy" name="strategy">
                        <option value="scalping" selected>Scalping</option>
                        <option value="swing">Swing Trading</option>
                        <option value="grid">Grid Trading</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Risk Per Trade (%):</label>
                    <input type="number" id="risk" name="risk" value="2" step="0.1" min="0.1" max="10" required>
                </div>
                
                <div class="form-group">
                    <label>Max Open Positions:</label>
                    <input type="number" id="max_positions" name="max_positions" value="3" min="1" max="10" required>
                </div>
                
                <div class="form-group">
                    <label>Stop Loss (%):</label>
                    <input type="number" id="stop_loss" name="stop_loss" value="1.5" step="0.1" min="0.1" required>
                </div>
                
                <div class="form-group">
                    <label>Take Profit (%):</label>
                    <input type="number" id="take_profit" name="take_profit" value="3.0" step="0.1" min="0.1" required>
                </div>
                
                <button type="submit" class="btn btn-primary">💾 Save Config</button>
                <button type="button" class="btn btn-secondary" onclick="loadConfig()">🔄 Load Config</button>
            </form>
        </div>
    </div>
    
    <script>
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert alert-${type}`;
            alert.style.display = 'block';
            setTimeout(() => { alert.style.display = 'none'; }, 3000);
        }
        
        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const config = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                const result = await response.json();
                showAlert(result.message, result.status);
            } catch (error) {
                showAlert('Error saving config', 'error');
            }
        });
        
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                for (const [key, value] of Object.entries(config)) {
                    const input = document.getElementById(key);
                    if (input) input.value = value;
                }
                showAlert('Config loaded successfully', 'success');
            } catch (error) {
                showAlert('Error loading config', 'error');
            }
        }
        
        // Load config on page load
        loadConfig();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Load configuration"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({'symbol': 'BTCUSDT', 'timeframe': '5m', 'strategy': 'scalping'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration"""
    try:
        config = request.json
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({'status': 'success', 'message': 'Config saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Config Manager running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
