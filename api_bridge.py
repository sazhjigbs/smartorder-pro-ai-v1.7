#!/usr/bin/env python3
"""
API Bridge: Connecte Ultimate Paper Trader au Dashboard
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = '/opt/smartorder-pro/data/ultimate_paper.db'

@app.route('/api/status', methods=['GET'])
def get_status():
    """Status du bot"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Last signal
        cursor.execute('SELECT * FROM signals ORDER BY timestamp DESC LIMIT 1')
        signal = cursor.fetchone()
        
        # Total trades
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_trades = cursor.fetchone()[0]
        
        # Total PnL
        cursor.execute('SELECT SUM(pnl) FROM trades')
        total_pnl = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return jsonify({
            'status': 'online',
            'mode': 'PAPER',
            'active_strategies': 1,
            'last_update': datetime.now().isoformat(),
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'last_signal': {
                'regime': signal[3] if signal else 'unknown',
                'action': signal[4] if signal else 'HOLD',
                'confidence': signal[5] if signal else 0.0,
                'price': signal[7] if signal else 0.0
            } if signal else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Positions actuelles"""
    try:
        # Charger depuis ultimate_paper_trader state
        # Pour l'instant retourne vide, sera rempli par le bot
        return jsonify({'positions': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Historique trades"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        limit = request.args.get('limit', 50, type=int)
        cursor.execute(f'SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}')
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'id': row[0],
                'timestamp': row[1],
                'symbol': row[2],
                'side': row[3],
                'amount': row[4],
                'price': row[5],
                'value': row[6],
                'pnl': row[7],
                'balance_after': row[8]
            })
        
        conn.close()
        return jsonify({'trades': trades})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Historique signaux"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        limit = request.args.get('limit', 20, type=int)
        cursor.execute(f'SELECT * FROM signals ORDER BY timestamp DESC LIMIT {limit}')
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'id': row[0],
                'timestamp': row[1],
                'symbol': row[2],
                'regime': row[3],
                'action': row[4],
                'confidence': row[5],
                'reason': row[6],
                'price': row[7],
                'rsi': row[8],
                'macd': row[9],
                'adx': row[10]
            })
        
        conn.close()
        return jsonify({'signals': signals})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiques globales"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # PnL stats
        cursor.execute('SELECT SUM(pnl), AVG(pnl), MAX(pnl), MIN(pnl) FROM trades')
        pnl_stats = cursor.fetchone()
        
        # Win rate
        cursor.execute('SELECT COUNT(*) FROM trades WHERE pnl > 0')
        wins = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM trades WHERE pnl < 0')
        losses = cursor.fetchone()[0]
        
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        conn.close()
        
        return jsonify({
            'total_pnl': pnl_stats[0] or 0.0,
            'avg_pnl': pnl_stats[1] or 0.0,
            'max_pnl': pnl_stats[2] or 0.0,
            'min_pnl': pnl_stats[3] or 0.0,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 API Bridge démarrée sur http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
