# === ULTIMATE PAPER TRADER INTEGRATION ===
import sqlite3
from fastapi import APIRouter

router = APIRouter()

DB_ULTIMATE = '/opt/smartorder-pro/data/ultimate_paper.db'

@router.get('/api/ultimate/status')
def get_ultimate_status():
    """Status du bot Ultimate Paper Trader"""
    try:
        conn = sqlite3.connect(DB_ULTIMATE)
        cursor = conn.cursor()
        
        # Last signal
        cursor.execute('SELECT * FROM signals ORDER BY timestamp DESC LIMIT 1')
        signal_row = cursor.fetchone()
        
        # Stats
        cursor.execute('SELECT COUNT(*), SUM(pnl) FROM trades')
        trades_count, total_pnl = cursor.fetchone()
        
        conn.close()
        
        signal = None
        if signal_row:
            signal = {
                'timestamp': signal_row[1],
                'regime': signal_row[3],
                'action': signal_row[4],
                'confidence': signal_row[5],
                'reason': signal_row[6],
                'price': signal_row[7],
                'rsi': signal_row[8]
            }
        
        return {
            'running': True,
            'last_signal': signal,
            'total_trades': trades_count or 0,
            'total_pnl': total_pnl or 0.0
        }
    except Exception as e:
        return {'running': False, 'error': str(e)}

@router.get('/api/ultimate/trades')
def get_ultimate_trades():
    """Trades du bot Ultimate"""
    try:
        conn = sqlite3.connect(DB_ULTIMATE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT 20')
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'timestamp': row[1],
                'symbol': row[2],
                'side': row[3],
                'amount': row[4],
                'price': row[5],
                'pnl': row[7]
            })
        
        conn.close()
        return {'trades': trades}
    except:
        return {'trades': []}
