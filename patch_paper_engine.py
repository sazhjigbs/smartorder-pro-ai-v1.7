#!/usr/bin/env python3
"""
Script pour corriger paper_trading_engine_realistic.py
Ajoute la fonction update_positions proprement
"""

ENGINE_FILE = '/opt/smartorder-pro/paper_trading_engine_realistic.py'
BACKUP_FILE = '/opt/smartorder-pro/paper_trading_engine_realistic.py.backup'

# Fonction à ajouter
UPDATE_POSITIONS_FUNCTION = '''
    def update_positions(self, trade_info):
        """Met à jour positions.json avec le dernier trade"""
        pos_file = CONFIG_DIR / 'positions.json'
        
        try:
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
            
            positions = {'positions': [], 'total_value': 0, 'last_update': datetime.now().isoformat()}
            if pos_file.exists():
                try:
                    with open(pos_file, 'r') as f:
                        positions = json.load(f)
                except:
                    pass
            
            if not isinstance(positions.get('positions'), list):
                positions['positions'] = []
            
            positions['positions'].append(position)
            positions['positions'] = positions['positions'][-50:]
            positions['last_update'] = datetime.now().isoformat()
            
            with open(pos_file, 'w') as f:
                json.dump(positions, f, indent=2)
                
        except Exception as e:
            print(f'[ERROR] update_positions: {e}')
'''

def main():
    import shutil
    
    # Backup
    shutil.copy(ENGINE_FILE, BACKUP_FILE)
    print(f'✅ Backup créé: {BACKUP_FILE}')
    
    # Lire fichier
    with open(ENGINE_FILE, 'r') as f:
        lines = f.readlines()
    
    # Nettoyer lignes cassées (entre 305 et 496)
    clean_lines = []
    skip_mode = False
    
    for i, line in enumerate(lines, 1):
        # Détecter zone cassée
        if i == 305 and '# Mise à jour positions.json' in line:
            skip_mode = True
            # Ajouter appel propre
            clean_lines.append('        self.update_positions(trade_info)\n')
            continue
        
        # Détecter fin zone cassée
        if skip_mode and (i > 450 or 'def ' in line or 'class ' in line):
            skip_mode = False
        
        if not skip_mode:
            clean_lines.append(line)
    
    # Trouver où insérer update_positions (après calculate_win_probability)
    insert_index = None
    for i, line in enumerate(clean_lines):
        if 'def calculate_win_probability' in line:
            # Trouver fin de cette fonction
            for j in range(i+1, len(clean_lines)):
                if clean_lines[j].strip() and not clean_lines[j].startswith(' ') or 'def ' in clean_lines[j]:
                    insert_index = j
                    break
            break
    
    if insert_index:
        clean_lines.insert(insert_index, UPDATE_POSITIONS_FUNCTION + '\n')
        print(f'✅ Fonction update_positions insérée à la ligne {insert_index}')
    
    # Écrire fichier corrigé
    with open(ENGINE_FILE, 'w') as f:
        f.writelines(clean_lines)
    
    print(f'✅ Fichier corrigé: {ENGINE_FILE}')
    print(f'📊 Lignes originales: {len(lines)}')
    print(f'📊 Lignes nettoyées: {len(clean_lines)}')
    
    # Test syntaxe
    import py_compile
    try:
        py_compile.compile(ENGINE_FILE, doraise=True)
        print('✅ Syntaxe Python valide')
    except Exception as e:
        print(f'❌ Erreur syntaxe: {e}')
        # Restaurer backup
        shutil.copy(BACKUP_FILE, ENGINE_FILE)
        print('🔄 Backup restauré')

if __name__ == '__main__':
    main()
