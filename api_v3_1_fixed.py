from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import os

app = FastAPI(title='SmartOrder PRO API', version='3.1.0-STABLE')

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
        return default if default is not None else {}

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
        'version': '3.1.0-STABLE',
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

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
    # Rétrocompatibilité Dashboard
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
    """Toutes les stratégies depuis trading_modes.json avec scores calculés"""
    try:
        data = read_json('trading_modes.json')
        if not data or not isinstance(data, dict):
            return {'strategies': [], 'mode': 'spot', 'count': 0}
        
        strategies = []
        
        # Lire signaux pour scoring
        signals = read_json('last_signals.json', {})
        rsi = signals.get('rsi', 50)
        macd = signals.get('macd', 0)
        bb_width = signals.get('bb_upper', 0) - signals.get('bb_lower', 0)
        
        for mode in ['spot', 'futures', 'hybrid']:
            mode_strategies = data.get('strategies', {}).get(mode, [])
            if not isinstance(mode_strategies, list):
                continue
                
            for strat in mode_strategies:
                # Calcul score basique
                base_score = 50
                if strat.get('enabled', False):
                    base_score += 20
                
                # Bonus selon RSI
                if 30 < rsi < 70:
                    base_score += 10
                elif rsi <= 30 and 'dca' in strat.get('id', '').lower():
                    base_score += 15
                
                strategies.append({
                    'id': strat.get('id', strat.get('label', 'unknown')),
                    'name': strat.get('label', strat.get('id', 'Unknown')),
                    'mode': mode,
                    'enabled': strat.get('enabled', False),
                    'active': strat.get('enabled', False),
                    'risk_level': strat.get('risk_profile', {}).get('level', 'medium'),
                    'indicators': strat.get('indicators', []),
                    'score': base_score,
                    'pnl': 0.0,
                    'ai_allowed': strat.get('ai_allowed', False),
                    'last_signal': strat.get('last_signal', 'HOLD'),
                    # Indicateurs détaillés
                    'rsi': round(rsi, 2) if rsi else None,
                    'macd': round(macd, 4) if macd else None,
                    'bb_width': round(bb_width, 2) if bb_width else None
                })
        
        return {
            'strategies': strategies,
            'mode': data.get('current_mode', 'spot'),
            'count': len(strategies)
        }
    except Exception as e:
        print(f'Error in get_strategies: {e}')
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/strategies/{strategy_id}/toggle')
async def toggle_strategy(strategy_id: str):
    """Toggle stratégie SANS authentification pour debug"""
    try:
        data = read_json('trading_modes.json')
        if not data or not isinstance(data, dict):
            raise HTTPException(status_code=500, detail='Invalid config format')
        
        updated = False
        new_state = None
        
        for mode in ['spot', 'futures', 'hybrid']:
            mode_strategies = data.get('strategies', {}).get(mode, [])
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
        
        if updated:
            if write_json('trading_modes.json', data):
                # Persistance
                state = read_json('strategies_state.json', {'strategies': {}})
                if not isinstance(state, dict):
                    state = {'strategies': {}}
                if 'strategies' not in state:
                    state['strategies'] = {}
                state['strategies'][strategy_id] = {
                    'enabled': new_state,
                    'updated_at': datetime.now().isoformat()
                }
                write_json('strategies_state.json', state)
                return {'status': 'success', 'strategy_id': strategy_id, 'enabled': new_state}
        
        raise HTTPException(status_code=404, detail=f'Strategy {strategy_id} not found')
    except HTTPException:
        raise
    except Exception as e:
        print(f'Toggle error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {str(e)}')

@app.get('/api/exchanges')
def get_exchanges():
    """États exchanges"""
    data = read_json('exchanges_state.json', {'exchanges': []})
    return data.get('exchanges', [])

@app.post('/api/exchanges/{exchange_id}/toggle')
async def toggle_exchange(exchange_id: str):
    """Toggle exchange SANS auth pour debug"""
    try:
        data = read_json('exchanges_state.json', {'exchanges': []})
        if not isinstance(data, dict):
            data = {'exchanges': []}
        
        updated = False
        new_state = None
        
        for exchange in data.get('exchanges', []):
            exch_id = exchange.get('id', '').lower()
            exch_name = exchange.get('name', '').lower().replace(' ', '_')
            
            if exch_id == exchange_id.lower() or exch_name == exchange_id.lower():
                exchange['enabled'] = not exchange.get('enabled', False)
                new_state = exchange['enabled']
                updated = True
                break
        
        if updated:
            data['last_update'] = datetime.now().isoformat()
            if write_json('exchanges_state.json', data):
                return {'status': 'success', 'exchange_id': exchange_id, 'enabled': new_state}
        
        raise HTTPException(status_code=404, detail=f'Exchange {exchange_id} not found')
    except HTTPException:
        raise
    except Exception as e:
        print(f'Toggle exchange error: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/signals')
def get_signals():
    """Derniers signaux"""
    data = read_json('last_signals.json', {})
    # Retourner comme liste pour compatibilité
    if isinstance(data, dict) and 'signals' not in data:
        return [data] if data else []
    return data.get('signals', [])

@app.get('/api/mode')
def get_mode():
    """Mode actuel"""
    data = read_json('trading_modes.json', {'current_mode': 'spot'})
    return {'mode': data.get('current_mode', 'spot')}

@app.post('/api/mode')
def set_mode(request: Dict[str, Any]):
    """Changer mode SANS auth"""
    mode = request.get('mode', 'spot')
    data = read_json('trading_modes.json', {})
    data['current_mode'] = mode
    if write_json('trading_modes.json', data):
        write_json('mode_state.json', {
            'current_mode': mode,
            'updated_at': datetime.now().isoformat()
        })
        return {'status': 'success', 'mode': mode}
    raise HTTPException(status_code=500, detail='Failed to update mode')

@app.get('/api/watchlist')
def get_watchlist():
    """Watchlist"""
    data = read_json('watchlist.json', {'coins': []})
    return data.get('coins', [])

@app.get('/api/market-regime')
def get_market_regime():
    """Market regime calculé depuis indicateurs réels"""
    signals = read_json('last_signals.json', {})
    
    # Calcul régime basique
    rsi = signals.get('rsi', 50)
    macd = signals.get('macd', 0)
    
    if rsi > 70:
        regime = 'BULLISH'
        volatility = 'HIGH'
    elif rsi < 30:
        regime = 'BEARISH'
        volatility = 'HIGH'
    else:
        regime = 'SIDEWAYS'
        volatility = 'MEDIUM'
    
    trend_strength = min(abs(rsi - 50) / 50, 1.0)
    ai_confidence = 0.7 + (trend_strength * 0.2)
    
    return {
        'regime': regime,
        'volatility': volatility,
        'trend_strength': round(trend_strength, 2),
        'ai_confidence': round(ai_confidence, 2),
        'rsi': round(rsi, 2) if rsi else None,
        'macd': round(macd, 4) if macd else None,
        'updated_at': signals.get('timestamp', datetime.now().isoformat())
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

@app.post('/api/strategies/simple-toggle')
async def simple_toggle(request: Dict[str, Any]):
    """Toggle simple sans bug"""
    try:
        strategy_id = request.get('strategy')
        action = request.get('action', 'toggle')
        state_file = CONFIG_PATH / 'strategies_state.json'
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                states = json.load(f)
        else:
            states = {'strategies': {}}
        
        if 'strategies' not in states:
            states['strategies'] = {}
        
        if action.lower() == 'enable':
            new_state = True
        elif action.lower() == 'disable':
            new_state = False
        else:
            current = states['strategies'].get(strategy_id, {}).get('enabled', False)
            new_state = not current
        
        states['strategies'][strategy_id] = {
            'enabled': new_state,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(state_file, 'w') as f:
            json.dump(states, f, indent=2)
        
        return {'status': 'success', 'strategy': strategy_id, 'enabled': new_state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/exchanges/simple-toggle')
async def simple_exchange_toggle(request: Dict[str, Any]):
    """Toggle exchange simple"""
    try:
        exchange_id = request.get('exchange')
        action = request.get('action', 'toggle')
        state_file = CONFIG_PATH / 'exchanges_state.json'
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                data = json.load(f)
        else:
            data = {'exchanges': []}
        
        found = False
        for exch in data.get('exchanges', []):
            if exch.get('id') == exchange_id or exch.get('name', '').lower().replace(' ', '_') == exchange_id.lower():
                if action.lower() == 'enable':
                    exch['enabled'] = True
                elif action.lower() == 'disable':
                    exch['enabled'] = False
                else:
                    exch['enabled'] = not exch.get('enabled', False)
                found = True
                break
        
        if found:
            data['last_update'] = datetime.now().isoformat()
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
            return {'status': 'success', 'exchange': exchange_id}
        
        raise HTTPException(status_code=404, detail='Exchange not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
