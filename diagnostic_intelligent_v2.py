#!/usr/bin/env python3
"""
🧠 DIAGNOSTIC INTELLIGENT MÉMOIRE v2.0
SmartOrder PRO - Système de supervision permanent avec anti-régression

Fonctionnalités:
- Base SQLite pour historique complet
- Détection automatique des régressions
- Validation de cohérence avant/après modifications
- Snapshot d'état stable (checksums)
- Rapport intelligent sans faux positifs
"""

import sqlite3
import subprocess
import json
import requests
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Configuration
DB_FILE = Path(__file__).parent / "diagnostic_memory.db"
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)

class DiagnosticMemory:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données"""
        cursor = self.conn.cursor()
        
        # Table des modules validés
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validated_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT UNIQUE NOT NULL,
                module_type TEXT NOT NULL,
                file_path TEXT,
                checksum TEXT,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'stable'
            )
        ''')
        
        # Table des erreurs corrigées
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resolved_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_signature TEXT UNIQUE NOT NULL,
                issue_type TEXT NOT NULL,
                description TEXT,
                resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolution_notes TEXT
            )
        ''')
        
        # Table de l'historique des audits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_checks INTEGER,
                passed_checks INTEGER,
                failed_checks INTEGER,
                new_issues INTEGER,
                resolved_issues INTEGER,
                status TEXT,
                report_json TEXT
            )
        ''')
        
        # Table des snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_name TEXT UNIQUE NOT NULL,
                snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_count INTEGER,
                total_size INTEGER,
                checksums_json TEXT,
                notes TEXT
            )
        ''')
        
        # Table des changements détectés
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detected_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                module_name TEXT,
                change_type TEXT,
                old_checksum TEXT,
                new_checksum TEXT,
                approved BOOLEAN DEFAULT 0,
                notes TEXT
            )
        ''')
        
        self.conn.commit()
    
    def is_issue_resolved(self, issue_signature: str) -> bool:
        """Vérifie si une issue a déjà été corrigée"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM resolved_issues WHERE issue_signature = ?",
            (issue_signature,)
        )
        return cursor.fetchone()[0] > 0
    
    def mark_issue_resolved(self, issue_signature: str, issue_type: str, 
                           description: str, notes: str = ""):
        """Marque une issue comme résolue"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO resolved_issues 
            (issue_signature, issue_type, description, resolution_notes)
            VALUES (?, ?, ?, ?)
        ''', (issue_signature, issue_type, description, notes))
        self.conn.commit()
    
    def validate_module(self, module_name: str, module_type: str, 
                       file_path: str = None):
        """Valide un module comme stable"""
        checksum = None
        if file_path and os.path.exists(file_path):
            checksum = self.get_file_checksum(file_path)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO validated_modules 
            (module_name, module_type, file_path, checksum, status)
            VALUES (?, ?, ?, ?, 'stable')
        ''', (module_name, module_type, file_path, checksum))
        self.conn.commit()
    
    def get_file_checksum(self, file_path: str) -> str:
        """Calcule le checksum SHA256 d'un fichier"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except:
            return None
    
    def detect_changes(self) -> List[Dict]:
        """Détecte les changements dans les modules validés"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT module_name, file_path, checksum 
            FROM validated_modules 
            WHERE status = 'stable' AND file_path IS NOT NULL
        ''')
        
        changes = []
        for module_name, file_path, old_checksum in cursor.fetchall():
            if not os.path.exists(file_path):
                changes.append({
                    'module': module_name,
                    'type': 'DELETED',
                    'path': file_path,
                    'severity': 'CRITICAL'
                })
            else:
                new_checksum = self.get_file_checksum(file_path)
                if new_checksum != old_checksum:
                    changes.append({
                        'module': module_name,
                        'type': 'MODIFIED',
                        'path': file_path,
                        'old_checksum': old_checksum[:8],
                        'new_checksum': new_checksum[:8],
                        'severity': 'WARNING'
                    })
                    
                    # Enregistrer le changement
                    cursor.execute('''
                        INSERT INTO detected_changes 
                        (module_name, change_type, old_checksum, new_checksum)
                        VALUES (?, ?, ?, ?)
                    ''', (module_name, 'MODIFIED', old_checksum, new_checksum))
        
        self.conn.commit()
        return changes
    
    def create_snapshot(self, snapshot_name: str, critical_files: List[str],
                       notes: str = ""):
        """Crée un snapshot de l'état actuel"""
        checksums = {}
        total_size = 0
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                checksums[file_path] = self.get_file_checksum(file_path)
                total_size += os.path.getsize(file_path)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO snapshots 
            (snapshot_name, file_count, total_size, checksums_json, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (snapshot_name, len(checksums), total_size, 
              json.dumps(checksums, indent=2), notes))
        self.conn.commit()
        
        return len(checksums)
    
    def save_audit(self, report: Dict):
        """Sauvegarde un audit dans l'historique"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO audit_history 
            (total_checks, passed_checks, failed_checks, new_issues, 
             resolved_issues, status, report_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.get('total_checks', 0),
            report.get('passed_checks', 0),
            report.get('failed_checks', 0),
            report.get('new_issues', 0),
            report.get('resolved_issues', 0),
            report.get('status', 'unknown'),
            json.dumps(report, indent=2)
        ))
        self.conn.commit()
    
    def get_stats(self) -> Dict:
        """Récupère les statistiques globales"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM validated_modules WHERE status='stable'")
        validated_modules = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resolved_issues")
        resolved_issues = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_history")
        total_audits = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT AVG(passed_checks * 100.0 / total_checks) 
            FROM audit_history 
            WHERE total_checks > 0
        ''')
        avg_success_rate = cursor.fetchone()[0] or 0
        
        return {
            'validated_modules': validated_modules,
            'resolved_issues': resolved_issues,
            'total_audits': total_audits,
            'avg_success_rate': round(avg_success_rate, 2)
        }
    
    def close(self):
        """Ferme la connexion"""
        self.conn.close()


def check_systemd_services() -> Dict:
    """Vérifie les services systemd"""
    services = {
        'smartorder-ai-learner': {'port': 8000, 'type': 'AI Learner'},
        'smartorder-auto-executor': {'port': 8001, 'type': 'AutoExecutor'},
        'nginx': {'port': [80, 443], 'type': 'Nginx'}
    }
    
    results = {}
    for service_name, info in services.items():
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True, timeout=5
            )
            is_active = result.stdout.strip() == 'active'
            results[service_name] = {
                'active': is_active,
                'port': info['port'],
                'type': info['type']
            }
        except Exception as e:
            results[service_name] = {
                'active': False,
                'port': info['port'],
                'type': info['type'],
                'error': str(e)
            }
    
    return results


def check_api_endpoints(port: int) -> Dict:
    """Teste les endpoints API"""
    endpoints = [
        ('/api/exchanges', 'exchanges'),
        ('/api/strategies?mode=SPOT', 'strategies_spot'),
        ('/api/strategies?mode=FUTURES', 'strategies_futures'),
        ('/api/positions', 'positions'),
        ('/api/funding-rates', 'funding_rates'),
        ('/api/market-regime', 'market_regime')
    ]
    
    results = {}
    for endpoint, key in endpoints:
        try:
            url = f'http://127.0.0.1:{port}{endpoint}'
            r = requests.get(url, timeout=5)
            data = r.json()
            
            count = 0
            if 'strategies' in data:
                count = len(data.get('strategies', []))
            elif 'exchanges' in data:
                count = len(data.get('exchanges', []))
            elif isinstance(data, list):
                count = len(data)
            
            results[key] = {
                'status': r.status_code,
                'count': count,
                'working': True
            }
        except Exception as e:
            results[key] = {
                'status': 'error',
                'count': 0,
                'working': False,
                'error': str(e)[:50]
            }
    
    return results


def check_critical_files() -> Tuple[List[str], List[str]]:
    """Vérifie la présence des fichiers critiques"""
    critical_files = [
        '/opt/smartorder-pro/api/main.py',
        '/opt/smartorder-pro/ai_core/ai_learner.py',
        '/opt/smartorder-pro/core/exchange_router.py',
        '/opt/smartorder-pro/core/multi_exchange_manager.py',
        '/opt/smartorder-pro/telegram/telegram_bot_pro.py',
        '/opt/smartorder-pro/web/dashboard.html',
        '/opt/smartorder-pro/config/strategies_state.json',
        '/opt/smartorder-pro/config/exchanges_state.json'
    ]
    
    present = []
    missing = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            present.append(file_path)
        else:
            missing.append(file_path)
    
    return present, missing


def main():
    print('=' * 80)
    print('🧠 DIAGNOSTIC INTELLIGENT MÉMOIRE v2.0 - SmartOrder PRO')
    print('=' * 80)
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    # Initialiser la mémoire
    memory = DiagnosticMemory()
    stats = memory.get_stats()
    
    print(f'📊 STATISTIQUES MÉMOIRE:')
    print(f'   Modules validés: {stats["validated_modules"]}')
    print(f'   Issues résolues: {stats["resolved_issues"]}')
    print(f'   Audits effectués: {stats["total_audits"]}')
    print(f'   Taux de succès moyen: {stats["avg_success_rate"]}%\n')
    
    report = {
        'total_checks': 0,
        'passed_checks': 0,
        'failed_checks': 0,
        'new_issues': 0,
        'resolved_issues': 0,
        'issues': [],
        'warnings': [],
        'status': 'unknown'
    }
    
    # 1. Vérifier les changements
    print('🔍 DÉTECTION DES CHANGEMENTS')
    print('-' * 80)
    changes = memory.detect_changes()
    if changes:
        print(f'   ⚠️  {len(changes)} changement(s) détecté(s):')
        for change in changes:
            print(f'      - {change["module"]}: {change["type"]} ({change["severity"]})')
        report['warnings'].extend(changes)
    else:
        print('   ✅ Aucun changement détecté\n')
    
    # 2. Services
    print('1️⃣  SERVICES SYSTEMD')
    print('-' * 80)
    services = check_systemd_services()
    report['total_checks'] += len(services)
    
    for service_name, info in services.items():
        status_icon = '✅' if info['active'] else '❌'
        print(f'   {status_icon} {service_name:30s} : {info["type"]:20s}')
        
        if info['active']:
            report['passed_checks'] += 1
            memory.validate_module(service_name, 'systemd_service')
        else:
            report['failed_checks'] += 1
            issue_sig = f'service_inactive_{service_name}'
            if not memory.is_issue_resolved(issue_sig):
                report['new_issues'] += 1
                report['issues'].append(f'Service {service_name} inactive')
    print()
    
    # 3. APIs
    print('2️⃣  ENDPOINTS API')
    print('-' * 80)
    for port in [8000, 8001]:
        print(f'   Port {port}:')
        api_results = check_api_endpoints(port)
        report['total_checks'] += len(api_results)
        
        for key, result in api_results.items():
            status_icon = '✅' if result['working'] else '❌'
            print(f'      {status_icon} {key:20s}: {result["count"]} items')
            
            if result['working']:
                report['passed_checks'] += 1
            else:
                report['failed_checks'] += 1
        print()
    
    # 4. Fichiers critiques
    print('3️⃣  FICHIERS CRITIQUES')
    print('-' * 80)
    present, missing = check_critical_files()
    report['total_checks'] += len(present) + len(missing)
    report['passed_checks'] += len(present)
    report['failed_checks'] += len(missing)
    
    print(f'   ✅ {len(present)} fichiers présents')
    if missing:
        print(f'   ❌ {len(missing)} fichiers manquants:')
        for file_path in missing:
            print(f'      - {file_path}')
            report['issues'].append(f'Fichier manquant: {file_path}')
    print()
    
    # Résumé
    print('=' * 80)
    print('📋 RÉSUMÉ')
    print('=' * 80)
    
    if report['failed_checks'] == 0:
        report['status'] = 'healthy'
        print('✅ SYSTÈME OPÉRATIONNEL - Aucun problème détecté\n')
    else:
        report['status'] = 'degraded'
        print(f'⚠️  {len(report["issues"])} PROBLÈME(S) DÉTECTÉ(S):\n')
        for i, issue in enumerate(report['issues'], 1):
            print(f'   {i}. {issue}')
        print()
    
    # Sauvegarder l'audit
    memory.save_audit(report)
    memory.close()
    
    print('💾 Audit sauvegardé dans la base de données')
    print('=' * 80)
    
    return report['status'] == 'healthy'


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
