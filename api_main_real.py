from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import os

app = FastAPI(title='SmartOrder PRO API', version='3.0.0-REAL-FILES-ONLY')

CONFIG_PATH = Path('/opt/smartorder-pro/config')
API_TOKEN = os.getenv('SMARTORDER_API_TOKEN', 'dev_token_12345')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def verify_token(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith('Bearer '):
        token = authorization.replace('Bearer ', '')
        if token == API_TOKEN:
            return token
    raise HTTPException(status_code=401, detail='Unauthorized')

def read_json(filename: str, default=None):
    try:
        with open(CONFIG_PATH / filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f'Error reading {filename}: {e}')
        return default or {}

def write_json(filename: str, data):
    try:
        with open(CONFIG_PATH / filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f'Error writing {filename}: {e}')
        return False

@app.get('/')
def root():
    return {
        'service': 'SmartOrder PRO API',
        'version': '3.0.0-REAL-FILES-ONLY',
        'status': 'online',
        'data_source': 'JSON files only',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
def health():
    return {'status': 'healthy'}

@app.get('/api/pnl')
def get_pnl():
    """PnL réel depuis pnl_tracker.json"""
    data = read_json('pnl_tracker.json', {
        'total_pnl': 0,
        'daily_pnl': 0,
        'weekly_pnl': 0,
        'trades_count': 0,
        'wins': 0,
        'losses': 0,
        'win_rate': 0,
        'profit_factor': 0,
        'last_update': None
    })
    # Rétrocompatibilité Dashboard : ajouter 'total' et 'daily'
    data['total'] = data.get('total_pnl', 0)
    data['daily'] = data.get('daily_pnl', 0)
    data['weekly'] = data.get('weekly_pnl', 0)
    return data

@app.get('/api/wallet')
def get_wallet():
    """Wallet réel depuis paper_wallet.json"""
    data = read_json('paper_wallet.json', {
        'balance_usdt': 10000,
        'total_pnl': 0,
        'open_positions': 0,
        'last_update': None
    })
    # Ajouter total_invested et total_trades
    data['total_invested'] = 10000.0
    data['total_trades'] = read_json('pnl_tracker.json', {}).get('trades_count', 0)
    return data

@app.get('/api/positions')
def get_positions():
    """Positions réelles depuis positions.json"""
    data = read_json('positions.json', {'positions': []})
    return data.get('positions', [])

@app.get('/api/strategies')
def get_strategies():
    """Toutes les stratégies depuis trading_modes.json"""
    try:
        data = read_json('trading_modes.json')
        strategies = []
        
        # Lire les derniers signaux pour calculer des scores basiques
        signals = read_json('last_signals.json', {})
        rsi = signals.get('rsi', 50)
        
        for mode in ['spot', 'futures', 'hybrid']:
            if mode in data.get('strategies', {}):
                for strat in data['strategies'][mode]:
                    # Calculer un score basique basé sur RSI et enabled
                    base_score = 50
                    if strat.get('enabled', False):
                        base_score += 20
                    if 30 < rsi < 70:  # RSI neutre
                        base_score += 10
                    elif rsi <= 30:  # RSI oversold = bon pour BUY
                        if 'dca' in strat.get('id', '').lower() or 'grid' in strat.get('id', '').lower():
                            base_score += 15
                    
                    strategies.append({
                        'id': strat.get('id', strat.get('label', 'unknown')),
                        'name': strat.get('label', strat.get('id', 'Unknown')),
                        'mode': mode,
                        'enabled': strat.get('enabled', False),
                        'active': strat.get('enabled', False),  # alias pour Dashboard
                        'risk_level': strat.get('risk_profile', {}).get('level', 'medium'),
                        'indicators': strat.get('indicators', []),
                        'score': base_score,
                        'pnl': 0.0,  # TODO: lier au PnL par stratégie
                        'ai_allowed': strat.get('ai_allowed', False),
                        'last_signal': strat.get('last_signal', 'HOLD')
                    })
        
        # Format attendu par Dashboard: {"strategies": [...], "mode": "spot"}
        return {
            'strategies': strategies,
            'mode': data.get('current_mode', 'spot'),
            'count': len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/strategies/{strategy_id}/toggle')
def toggle_strategy(strategy_id: str, token: str = Depends(verify_token)):
    """Toggle stratégie avec persistance"""
    try:
        data = read_json('trading_modes.json')
        if not isinstance(data, dict):
            raise HTTPException(status_code=500, detail='Invalid trading_modes.json format')
        
        updated = False
        new_state = None
        
        for mode in ['spot', 'futures', 'hybrid']:
            if mode in data.get('strategies', {}):
                mode_strategies = data['strategies'][mode]
                if not isinstance(mode_strategies, list):
                    continue
                for strat in mode_strategies:
                    if strat.get('id') == strategy_id or strat.get('label') == strategy_id:
                        strat['enabled'] = not strat.get('enabled', False)
                        new_state = strat['enabled']
                        updated = True
                        break
            if updated:
                break
        
        if updated and write_json('trading_modes.json', data):
            # Mettre à jour strategies_state.json pour persistance
            state = read_json('strategies_state.json', {'strategies': {}})
            if 'strategies' not in state:
                state['strategies'] = {}
            state['strategies'][strategy_id] = {'enabled': new_state, 'updated_at': datetime.now().isoformat()}
            write_json('strategies_state.json', state)
            return {'status': 'success', 'strategy_id': strategy_id, 'enabled': new_state}
        
        raise HTTPException(status_code=404, detail=f'Strategy {strategy_id} not found')
    except HTTPException:
        raise
    except Exception as e:
        print(f'Toggle strategy error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {str(e)}')

@app.get('/api/signals')
def get_signals():
    """Derniers signaux depuis last_signals.json"""
    data = read_json('last_signals.json', {'signals': []})
    return data.get('signals', [])

@app.get('/api/exchanges')
def get_exchanges():
    """États exchanges depuis exchanges_state.json"""
    data = read_json('exchanges_state.json', {'exchanges': []})
    return data.get('exchanges', [])

@app.post('/api/exchanges/{exchange_id}/toggle')
def toggle_exchange(exchange_id: str, token: str = Depends(verify_token)):
    """Toggle exchange avec persistance"""
    try:
        data = read_json('exchanges_state.json', {'exchanges': []})
        updated = False
        new_state = None
        
        for exchange in data.get('exchanges', []):
            if exchange.get('id') == exchange_id or exchange.get('name', '').lower().replace(' ', '_') == exchange_id.lower():
                exchange['enabled'] = not exchange.get('enabled', False)
                new_state = exchange['enabled']
                updated = True
                break
        
        if updated:
            data['last_update'] = datetime.now().isoformat()
            if write_json('exchanges_state.json', data):
                return {'status': 'success', 'exchange_id': exchange_id, 'enabled': new_state}
        
        raise HTTPException(status_code=404, detail='Exchange not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/mode')
def get_mode():
    """Mode actuel"""
    data = read_json('trading_modes.json', {'current_mode': 'spot'})
    return {'mode': data.get('current_mode', 'spot')}

@app.post('/api/mode')
def set_mode(request: Dict[str, Any], token: str = Depends(verify_token)):
    """Changer mode avec persistance"""
    mode = request.get('mode', 'spot')
    data = read_json('trading_modes.json', {})
    data['current_mode'] = mode
    if write_json('trading_modes.json', data):
        # Persistance dans mode_state.json
        write_json('mode_state.json', {'current_mode': mode, 'updated_at': datetime.now().isoformat()})
        return {'status': 'success', 'mode': mode}
    raise HTTPException(status_code=500, detail='Failed to update mode')

@app.get('/api/watchlist')
def get_watchlist():
    """Watchlist"""
    data = read_json('watchlist.json', {'coins': []})
    return data.get('coins', [])

@app.get('/api/market-regime')
def get_market_regime():
    """Market regime depuis diagnostic ou calcul réel"""
    data = read_json('diagnostic_latest.json', {})
    return {
        'regime': data.get('market_regime', 'SIDEWAYS'),
        'volatility': data.get('volatility', 'MEDIUM'),
        'trend_strength': data.get('trend_strength', 0.5),
        'ai_confidence': data.get('ai_confidence', 0.7),
        'updated_at': data.get('last_update', datetime.now().isoformat())
    }

# Static files
web_path = Path('/opt/smartorder-pro/web')
if web_path.exists():
    app.mount('/static', StaticFiles(directory=str(web_path)), name='static')
    
    dashboard_file = web_path / 'dashboard.html'
    if dashboard_file.exists():
        @app.get('/dashboard')
        def serve_dashboard():
            return FileResponse(str(dashboard_file))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
