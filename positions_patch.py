    def update_positions(self, trade_info):
        """Met à jour positions.json avec le dernier trade"""
        pos_file = CONFIG_DIR / 'positions.json'
        
        try:
            # Créer position
            position = {
                'symbol': trade_info['symbol'],
                'strategy': 'Paper Realistic',
                'amount': trade_info['amount_usdt'],
                'entry': trade_info['price'],
                'current': trade_info['price'],
                'sl': trade_info['price'] * 0.98,
                'tp': trade_info['price'] * 1.03,
                'pnl': trade_info['pnl'],
                'side': trade_info['side'],
                'timestamp': trade_info['timestamp']
            }
            
            # Charger positions existantes
            positions = {'positions': [], 'total_value': 0, 'last_update': datetime.now().isoformat()}
            if pos_file.exists():
                try:
                    with open(pos_file, 'r') as f:
                        positions = json.load(f)
                except:
                    pass
            
            # Ajouter nouvelle position
            if not isinstance(positions.get('positions'), list):
                positions['positions'] = []
            
            positions['positions'].append(position)
            positions['positions'] = positions['positions'][-50:]
            positions['last_update'] = datetime.now().isoformat()
            
            # Sauvegarder
            with open(pos_file, 'w') as f:
                json.dump(positions, f, indent=2)
                
        except Exception as e:
            print(f'[ERROR] update_positions: {e}')
