#!/usr/bin/env python3
"""
UPDATE: Watchlist Sync v2.1.1
Date: 2025-10-31
Description: Synchronisation watchlist avec format standard et integration bot
"""

import json
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path("/opt/smartorder-pro/config")
WATCHLIST_FILE = CONFIG_DIR / "watchlist.json"

def fix_watchlist_format():
    """Convertit watchlist au format standard (list)"""
    print("🔧 Correction format watchlist...")
    
    # Backup
    if WATCHLIST_FILE.exists():
        backup_file = CONFIG_DIR / f"watchlist_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(WATCHLIST_FILE, 'r') as f:
            backup_data = f.read()
        with open(backup_file, 'w') as f:
            f.write(backup_data)
        print(f"✅ Backup: {backup_file}")
    
    # Lire format actuel
    with open(WATCHLIST_FILE, 'r') as f:
        current = json.load(f)
    
    # Extraire coins
    if isinstance(current, dict) and "coins" in current:
        coins_list = current["coins"]
    elif isinstance(current, list):
        coins_list = current
    else:
        coins_list = ["BTC/USDT", "ETH/USDT"]  # Default
    
    # Ecrire format standard
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(coins_list, f, indent=2)
    
    print(f"✅ Watchlist standardisée: {len(coins_list)} coins")
    print(f"   Coins: {', '.join(coins_list)}")
    
    return coins_list

def create_watchlist_metadata():
    """Cree fichier metadata pour tracking modifications"""
    metadata_file = CONFIG_DIR / "watchlist_metadata.json"
    
    with open(WATCHLIST_FILE, 'r') as f:
        coins = json.load(f)
    
    metadata = {
        "last_update": datetime.now().isoformat(),
        "coin_count": len(coins),
        "coins": coins,
        "user_modified": True
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata créée: {metadata_file}")
    return metadata

def test_watchlist():
    """Teste la watchlist"""
    print("\n🧪 Test watchlist...")
    
    with open(WATCHLIST_FILE, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print("❌ Format invalide")
        return False
    
    print(f"✅ Format valide: {len(data)} coins")
    
    for coin in data:
        if "/" not in coin:
            print(f"⚠️  Format coin invalide: {coin}")
        else:
            print(f"   ✓ {coin}")
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("UPDATE: Watchlist Sync v2.1.1")
    print("="*60)
    
    # Fix format
    coins = fix_watchlist_format()
    
    # Create metadata
    metadata = create_watchlist_metadata()
    
    # Test
    test_watchlist()
    
    print("\n" + "="*60)
    print("✅ UPDATE COMPLETE")
    print("="*60)
