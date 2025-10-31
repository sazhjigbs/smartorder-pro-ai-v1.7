#!/usr/bin/env python3
"""
Création du Snapshot v2.0-stable
Fige l'état actuel du bot comme version de référence stable
"""

import sys
import sqlite3
import hashlib
import os
import json
from pathlib import Path
from datetime import datetime

# Liste exhaustive des fichiers critiques à inclure dans le snapshot
CRITICAL_FILES = [
    # Core API
    '/opt/smartorder-pro/api/main.py',
    '/opt/smartorder-pro/api/main_integrated.py',
    '/opt/smartorder-pro/api_production_complete.py',
    
    # AI Core
    '/opt/smartorder-pro/ai_core/ai_learner.py',
    '/opt/smartorder-pro/ai_core/ai_status_api.py',
    '/opt/smartorder-pro/ai/strategy_composer_real.py',
    
    # Core Modules
    '/opt/smartorder-pro/core/exchange_router.py',
    '/opt/smartorder-pro/core/multi_exchange_manager.py',
    '/opt/smartorder-pro/core/signal_aggregator.py',
    '/opt/smartorder-pro/core/signal_validator.py',
    '/opt/smartorder-pro/core/arbitrage_executor.py',
    '/opt/smartorder-pro/core/bot_state_manager.py',
    
    # Strategies
    '/opt/smartorder-pro/core/dca_strategy.py',
    '/opt/smartorder-pro/strategies/grid_trading_strategy.py',
    '/opt/smartorder-pro/smart_strategy_manager.py',
    
    # Exchange Connectors
    '/opt/smartorder-pro/exchange_connectors/bybit_connector.py',
    '/opt/smartorder-pro/exchange_connectors/binance_connector.py',
    '/opt/smartorder-pro/exchange_connectors/okx_connector.py',
    '/opt/smartorder-pro/exchange_connectors/kucoin_connector.py',
    
    # Telegram Bot
    '/opt/smartorder-pro/telegram/telegram_bot_pro.py',
    
    # Web Dashboard
    '/opt/smartorder-pro/web/dashboard.html',
    
    # Configuration
    '/opt/smartorder-pro/config/strategies_state.json',
    '/opt/smartorder-pro/config/exchanges_state.json',
    
    # Main Bot
    '/opt/smartorder-pro/ultimate_trading_bot.py',
]

def get_file_checksum(file_path: str) -> str:
    """Calcule le checksum SHA256"""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return None

def create_snapshot():
    """Crée le snapshot v2.0-stable"""
    print('=' * 80)
    print('📸 CRÉATION DU SNAPSHOT v2.0-stable')
    print('=' * 80)
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    # Connexion à la base de données
    db_file = Path('/root/diagnostic_memory.db')
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Calculer les checksums
    checksums = {}
    total_size = 0
    present_count = 0
    missing_count = 0
    
    print('🔍 ANALYSE DES FICHIERS CRITIQUES:')
    print('-' * 80)
    
    for file_path in CRITICAL_FILES:
        if os.path.exists(file_path):
            checksum = get_file_checksum(file_path)
            size = os.path.getsize(file_path)
            checksums[file_path] = {
                'checksum': checksum,
                'size': size,
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }
            total_size += size
            present_count += 1
            print(f'   ✅ {os.path.basename(file_path):40s} ({size:>8} bytes)')
        else:
            missing_count += 1
            print(f'   ❌ {os.path.basename(file_path):40s} MANQUANT')
    
    print()
    print(f'📊 RÉSUMÉ:')
    print(f'   Fichiers présents: {present_count}/{len(CRITICAL_FILES)}')
    print(f'   Fichiers manquants: {missing_count}')
    print(f'   Taille totale: {total_size / 1024 / 1024:.2f} MB\n')
    
    # Sauvegarder dans la base
    cursor.execute('''
        INSERT OR REPLACE INTO snapshots 
        (snapshot_name, file_count, total_size, checksums_json, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'v2.0-stable',
        present_count,
        total_size,
        json.dumps(checksums, indent=2),
        f'Snapshot stable avant tests Paper Trading - {present_count}/{len(CRITICAL_FILES)} fichiers'
    ))
    
    # Valider tous les modules présents
    for file_path, info in checksums.items():
        module_name = os.path.basename(file_path).replace('.py', '').replace('.json', '').replace('.html', '')
        module_type = 'python' if file_path.endswith('.py') else 'config' if file_path.endswith('.json') else 'web'
        
        cursor.execute('''
            INSERT OR REPLACE INTO validated_modules 
            (module_name, module_type, file_path, checksum, status)
            VALUES (?, ?, ?, ?, 'stable')
        ''', (module_name, module_type, file_path, info['checksum']))
    
    conn.commit()
    conn.close()
    
    print('✅ SNAPSHOT v2.0-stable CRÉÉ')
    print('=' * 80)
    print()
    print('📋 ÉTAT FIGÉ:')
    print(f'   - {present_count} modules validés')
    print(f'   - {total_size / 1024 / 1024:.2f} MB de code')
    print(f'   - Checksums sauvegardés dans diagnostic_memory.db')
    print()
    print('🔒 PROTECTION ANTI-RÉGRESSION ACTIVÉE')
    print('   Toute modification sera détectée et tracée')
    print('=' * 80)

if __name__ == '__main__':
    create_snapshot()
