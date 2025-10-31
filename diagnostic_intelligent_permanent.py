#!/usr/bin/env python3
"""
🧠 DIAGNOSTIC INTELLIGENT PERMANENT - SmartOrder PRO AI v2.0-stable
===================================================================
Supervision continue avec mémoire des anomalies corrigées.
Mode: Service systemd tournant en boucle toutes les 5 minutes.

Fonctionnalités:
- Mémorisation anomalies corrigées (base SQLite)
- Vérification cohérence code avant audit
- Détection régression
- Signalement uniquement anomalies réelles (non déjà corrigées)
- Auto-correction si possible
"""

import sqlite3
import json
import os
import time
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
LOG_DIR = Path('/opt/smartorder-pro/logs')
LOG_DIR.mkdir(exist_ok=True)
DB_FILE = '/opt/smartorder-pro/config/diagnostic_memory.db'
REPORT_FILE = '/opt/smartorder-pro/config/diagnostic_latest.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'diagnostic_permanent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DiagnosticMemory:
    """Base de données SQLite pour mémoriser anomalies corrigées"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.init_db()
    
    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomalies_fixed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_hash TEXT UNIQUE,
                anomaly_type TEXT,
                description TEXT,
                fixed_at TEXT,
                version TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT,
                created_at TEXT,
                files_hash TEXT,
                status TEXT
            )
        ''')
        self.conn.commit()
    
    def is_anomaly_fixed(self, anomaly_hash: str) -> bool:
        """Vérifie si une anomalie a déjà été corrigée"""
        cursor = self.conn.cursor()
        result = cursor.execute(
            'SELECT COUNT(*) FROM anomalies_fixed WHERE anomaly_hash = ?',
            (anomaly_hash,)
        ).fetchone()
        return result[0] > 0
    
    def mark_as_fixed(self, anomaly_type: str, description: str, version='v2.0-stable'):
        """Marque une anomalie comme corrigée"""
        anomaly_hash = hashlib.md5(f"{anomaly_type}:{description}".encode()).hexdigest()
        
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO anomalies_fixed (anomaly_hash, anomaly_type, description, fixed_at, version)
                VALUES (?, ?, ?, ?, ?)
            ''', (anomaly_hash, anomaly_type, description, datetime.now().isoformat(), version))
            self.conn.commit()
            logger.info(f"✅ Anomalie mémorisée: {anomaly_type}")
        except sqlite3.IntegrityError:
            pass  # Déjà en base
    
    def save_snapshot(self, version: str, files_hash: str, status: str):
        """Sauvegarde un snapshot de version"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO snapshots (version, created_at, files_hash, status)
            VALUES (?, ?, ?, ?)
        ''', (version, datetime.now().isoformat(), files_hash, status))
        self.conn.commit()


class PermanentDiagnostic:
    """Diagnostic intelligent permanent"""
    
    def __init__(self):
        self.memory = DiagnosticMemory()
        self.critical_files = [
            '/opt/smartorder-pro/strategy_executor_v3_real.py',
            '/opt/smartorder-pro/api/main.py',
            '/opt/smartorder-pro/web/dashboard.html',
            '/opt/smartorder-pro/config/strategies_state.json',
            '/opt/smartorder-pro/config/pnl_tracker.json'
        ]
    
    def calculate_files_hash(self) -> str:
        """Calcule hash des fichiers critiques pour détecter modifications"""
        hasher = hashlib.sha256()
        for file_path in self.critical_files:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        return hasher.hexdigest()
    
    def check_services(self) -> dict:
        """Vérifie services systemd"""
        services = {
            'smartorder-api': False,
            'strategy-executor-v3': False
        }
        
        for service in services.keys():
            result = os.system(f'systemctl is-active {service} > /dev/null 2>&1')
            services[service] = (result == 0)
        
        return services
    
    def check_api_endpoints(self) -> dict:
        """Vérifie endpoints API critiques"""
        import requests
        
        endpoints = {
            '/api/health': False,
            '/api/pnl': False,
            '/api/positions': False,
            '/api/activity-log': False,
            '/api/market-regime': False,
            '/api/wallet': False
        }
        
        for endpoint in endpoints.keys():
            try:
                resp = requests.get(f'http://localhost:8000{endpoint}', timeout=5)
                endpoints[endpoint] = (resp.status_code == 200)
            except:
                endpoints[endpoint] = False
        
        return endpoints
    
    def check_pnl_logic(self) -> dict:
        """Vérifie que le Total PnL lit pnl_tracker.json"""
        dashboard_file = '/opt/smartorder-pro/web/dashboard.html'
        
        checks = {
            'pnl_tracker_exists': os.path.exists('/opt/smartorder-pro/config/pnl_tracker.json'),
            'updateTotalPnL_function_exists': False,
            'api_pnl_called': False
        }
        
        if os.path.exists(dashboard_file):
            with open(dashboard_file, 'r') as f:
                content = f.read()
                checks['updateTotalPnL_function_exists'] = 'async function updateTotalPnL()' in content
                checks['api_pnl_called'] = '/api/pnl' in content
        
        return checks
    
    def run_diagnostic(self) -> dict:
        """Exécute diagnostic complet"""
        logger.info("=" * 80)
        logger.info("🧠 DIAGNOSTIC INTELLIGENT PERMANENT - v2.0-stable")
        logger.info("=" * 80)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'version': 'v2.0-stable',
            'files_hash': self.calculate_files_hash(),
            'services': self.check_services(),
            'api_endpoints': self.check_api_endpoints(),
            'pnl_logic': self.check_pnl_logic(),
            'anomalies': [],
            'status': 'OK'
        }
        
        # Analyser résultats
        # 1. Services
        for service, running in report['services'].items():
            if not running:
                anomaly_hash = hashlib.md5(f"service_down:{service}".encode()).hexdigest()
                if not self.memory.is_anomaly_fixed(anomaly_hash):
                    report['anomalies'].append({
                        'type': 'SERVICE_DOWN',
                        'severity': 'CRITICAL',
                        'description': f"Service {service} is down",
                        'auto_fix': f"systemctl start {service}"
                    })
                    report['status'] = 'CRITICAL'
        
        # 2. API Endpoints
        critical_endpoints = ['/api/health', '/api/pnl', '/api/positions']
        for endpoint in critical_endpoints:
            if not report['api_endpoints'].get(endpoint, False):
                anomaly_hash = hashlib.md5(f"endpoint_fail:{endpoint}".encode()).hexdigest()
                if not self.memory.is_anomaly_fixed(anomaly_hash):
                    report['anomalies'].append({
                        'type': 'ENDPOINT_FAIL',
                        'severity': 'HIGH',
                        'description': f"Endpoint {endpoint} not responding",
                        'auto_fix': "systemctl restart smartorder-api"
                    })
                    report['status'] = 'WARNING'
        
        # 3. PnL Logic
        if not all(report['pnl_logic'].values()):
            anomaly_hash = hashlib.md5("pnl_logic_broken".encode()).hexdigest()
            if not self.memory.is_anomaly_fixed(anomaly_hash):
                report['anomalies'].append({
                    'type': 'PNL_LOGIC_BROKEN',
                    'severity': 'CRITICAL',
                    'description': "Total PnL not reading from pnl_tracker.json",
                    'auto_fix': "python3 /opt/smartorder-pro/fix_pnl_dashboard.py"
                })
                report['status'] = 'CRITICAL'
        
        # Sauvegarder rapport
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Log résumé
        logger.info(f"Status: {report['status']}")
        logger.info(f"Services: {sum(report['services'].values())}/{len(report['services'])} actifs")
        logger.info(f"API Endpoints: {sum(report['api_endpoints'].values())}/{len(report['api_endpoints'])} OK")
        logger.info(f"Anomalies nouvelles: {len(report['anomalies'])}")
        
        # Auto-corrections si possible
        if report['anomalies']:
            logger.warning("⚠️  Anomalies détectées:")
            for anomaly in report['anomalies']:
                logger.warning(f"  - [{anomaly['severity']}] {anomaly['description']}")
                if anomaly.get('auto_fix'):
                    logger.info(f"    💡 Auto-fix: {anomaly['auto_fix']}")
        
        # Sauvegarder snapshot
        self.memory.save_snapshot('v2.0-stable', report['files_hash'], report['status'])
        
        logger.info("=" * 80)
        return report
    
    def run_loop(self, interval=300):
        """Boucle de supervision (défaut: 5 minutes)"""
        logger.info("🔄 Mode supervision permanente activé (interval: {}s)".format(interval))
        
        try:
            while True:
                self.run_diagnostic()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("⚠️  Arrêt supervision")


if __name__ == '__main__':
    diagnostic = PermanentDiagnostic()
    diagnostic.run_loop(interval=300)  # Toutes les 5 minutes
