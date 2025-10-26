#!/usr/bin/env python3
"""
💾 SAFELOGIC SmartOrder PRO — Auto Backup
Optimisé pour VPS avec RAM limitée (859MB/3919MB)
"""

import os
import time
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

# Config optimisée VPS
BACKUP_DIR = "/opt/smartorder-backups"  # VPS path
SOURCE_DIR = "/opt/smartorder-pro"
MAX_BACKUPS = 3  # Garde seulement 3 backups (économie disque)
BACKUP_INTERVAL_HOURS = 6

# Exclusions pour économiser espace
EXCLUDE_PATTERNS = [
    '__pycache__',
    '*.pyc',
    '.git',
    'node_modules',
    'venv',
    '*.log',
    'logs/*',
    'backups/*',
    '.pytest_cache'
]

class LightweightBackup:
    """Backup ultra-léger pour VPS faible RAM"""
    
    def __init__(self):
        self.backup_dir = Path(BACKUP_DIR)
        self.source_dir = Path(SOURCE_DIR)
        
        # Crée dossier backup
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def should_exclude(self, path):
        """Check si fichier doit être exclu"""
        path_str = str(path)
        for pattern in EXCLUDE_PATTERNS:
            if pattern.replace('*', '') in path_str:
                return True
        return False
    
    def create_backup(self):
        """Crée backup compressé (économie RAM)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"smartorder_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        print(f"💾 Creating backup: {backup_name}")
        
        try:
            # Utilise tar.gz pour économiser RAM et disque
            with tarfile.open(backup_path, "w:gz") as tar:
                for item in self.source_dir.rglob("*"):
                    if item.is_file() and not self.should_exclude(item):
                        # Ajoute fichier par fichier (économie RAM)
                        arcname = item.relative_to(self.source_dir)
                        tar.add(item, arcname=arcname)
            
            # Vérifie taille
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            print(f"✅ Backup created: {backup_name} ({size_mb:.1f} MB)")
            
            # Nettoie vieux backups
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return False
    
    def cleanup_old_backups(self):
        """Garde seulement les N derniers backups"""
        try:
            backups = sorted(self.backup_dir.glob("smartorder_backup_*.tar.gz"))
            
            if len(backups) > MAX_BACKUPS:
                for old_backup in backups[:-MAX_BACKUPS]:
                    old_backup.unlink()
                    print(f"🗑️ Removed old backup: {old_backup.name}")
                    
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")
    
    def get_backup_status(self):
        """Status backups actuels"""
        backups = sorted(self.backup_dir.glob("smartorder_backup_*.tar.gz"))
        
        total_size = sum(b.stat().st_size for b in backups) / (1024 * 1024)
        
        return {
            "count": len(backups),
            "total_size_mb": round(total_size, 2),
            "latest": backups[-1].name if backups else None
        }

def run_once():
    """Exécute backup une fois"""
    backup = LightweightBackup()
    backup.create_backup()
    
    status = backup.get_backup_status()
    print(f"\n📊 Backup Status:")
    print(f"   Count: {status['count']}/{MAX_BACKUPS}")
    print(f"   Total: {status['total_size_mb']} MB")
    print(f"   Latest: {status['latest']}")

def main():
    """Mode daemon (pour systemd)"""
    print("🛡️ Auto-Backup Guardian started")
    print(f"📁 Source: {SOURCE_DIR}")
    print(f"💾 Backup: {BACKUP_DIR}")
    print(f"⏱️ Interval: {BACKUP_INTERVAL_HOURS}h")
    
    backup = LightweightBackup()
    
    while True:
        try:
            backup.create_backup()
        except Exception as e:
            print(f"💥 Backup error: {str(e)}")
        
        # Attends prochaine backup
        time.sleep(BACKUP_INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
    else:
        main()
