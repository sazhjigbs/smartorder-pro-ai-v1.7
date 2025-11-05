@app.get('/api/strategies')
def get_strategies(mode: Optional[str] = None):
    """Stratégies filtrées par mode avec scores calculés"""
    try:
        data = read_json('trading_modes.json')
        if not data or not isinstance(data, dict):
            return {'strategies': [], 'mode': 'spot', 'count': 0}
        
        strategies = []
        
        # Signaux pour scoring
        signals = read_json('last_signals.json', {})
        rsi = signals.get('rsi', 50)
        macd = signals.get('macd', 0)
        bb_width = signals.get('bb_upper', 0) - signals.get('bb_lower', 0)
        
        # Mode actuel
        current_mode = data.get('current_mode', 'spot').lower()
        filter_mode = mode.lower() if mode else current_mode
        
        # Modes à scanner
        if filter_mode in ['spot', 'futures', 'hybrid']:
            modes_to_scan = [filter_mode]
        else:
            modes_to_scan = ['spot', 'futures', 'hybrid']
        
        for mode_name in modes_to_scan:
            mode_strategies = data.get('strategies', {}).get(mode_name, [])
            if not isinstance(mode_strategies, list):
                continue
                
            for strat in mode_strategies:
                base_score = 50
                if strat.get('enabled', False):
                    base_score += 20
                
                if 30 < rsi < 70:
                    base_score += 10
                elif rsi <= 30 and 'dca' in strat.get('id', '').lower():
                    base_score += 15
                
                strategies.append({
                    'id': strat.get('id', strat.get('label', 'unknown')),
                    'name': strat.get('label', strat.get('id', 'Unknown')),
                    'mode': mode_name,
                    'enabled': strat.get('enabled', False),
                    'active': strat.get('enabled', False),
                    'risk_level': strat.get('risk_profile', {}).get('level', 'medium'),
                    'indicators': strat.get('indicators', []),
                    'score': base_score,
                    'pnl': 0.0,
                    'ai_allowed': strat.get('ai_allowed', False),
                    'last_signal': strat.get('last_signal', 'HOLD'),
                    'rsi': round(rsi, 2) if rsi else None,
                    'macd': round(macd, 4) if macd else None,
                    'bb_width': round(bb_width, 2) if bb_width else None
                })
        
        return {
            'strategies': strategies,
            'mode': filter_mode,
            'count': len(strategies),
            'filtered': filter_mode != 'all'
        }
    except Exception as e:
        print(f'Error in get_strategies: {e}')
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
