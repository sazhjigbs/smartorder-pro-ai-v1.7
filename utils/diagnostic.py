# -*- coding: utf-8 -*-
"""
Diagnostic Complet du Bot
Verifie la sante de tous les modules avant deploiement

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


class BotDiagnostic:
    """
    Système de diagnostic complet pour le bot
    
    Vérifie:
    - Configuration (.env)
    - Exchanges connectivity
    - Database & encryption
    - Security modules
    - Monitoring systems
    - Logs & directories
    """
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'checks': {},
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
    
    def run_all_checks(self):
        """Run all diagnostic checks"""
        LOG.info("🔍 Starting diagnostic checks...")
        
        # Environment
        self.check_environment()
        
        # Configuration
        self.check_configuration()
        
        # Exchanges
        self.check_exchanges()
        
        # Database
        self.check_database()
        
        # Security
        self.check_security()
        
        # Monitoring
        self.check_monitoring()
        
        # Logs
        self.check_logs()
        
        # Dependencies
        self.check_dependencies()
        
        # Final status
        self._compute_overall_status()
        
        LOG.info("✅ Diagnostic complete!")
        
        return self.results
    
    def check_environment(self):
        """Check environment variables"""
        LOG.info("Checking environment...")
        
        required_vars = [
            'ACTIVE_EXCHANGE',
            'PAPER_TRADING',
            'USE_TESTNET'
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            self.results['checks']['environment'] = {
                'status': 'FAIL',
                'message': f'Missing variables: {", ".join(missing)}'
            }
            self.results['errors'].append(f'Environment: Missing {len(missing)} variables')
        else:
            self.results['checks']['environment'] = {
                'status': 'PASS',
                'message': 'All required environment variables present'
            }
    
    def check_configuration(self):
        """Check configuration files"""
        LOG.info("Checking configuration files...")
        
        config_files = [
            '.env',
            'config/bot_config.json',
            'config/exchanges.json'
        ]
        
        missing = []
        for file in config_files:
            if not Path(file).exists():
                missing.append(file)
        
        if missing:
            self.results['checks']['configuration'] = {
                'status': 'FAIL',
                'message': f'Missing files: {", ".join(missing)}'
            }
            self.results['errors'].append(f'Config: Missing {len(missing)} files')
        else:
            self.results['checks']['configuration'] = {
                'status': 'PASS',
                'message': 'All configuration files present'
            }
    
    def check_exchanges(self):
        """Check exchange connectivity"""
        LOG.info("Checking exchange connections...")
        
        try:
            from core.unified_trading_manager import UnifiedTradingManager
            
            manager = UnifiedTradingManager()
            
            exchanges_status = {}
            for exchange_name, connector in manager.connectors.items():
                try:
                    result = connector.test_connection()
                    exchanges_status[exchange_name] = result.get('success', False)
                except Exception as e:
                    exchanges_status[exchange_name] = False
                    LOG.error(f"Exchange {exchange_name} failed: {e}")
            
            total = len(exchanges_status)
            working = sum(1 for v in exchanges_status.values() if v)
            
            if working == 0:
                self.results['checks']['exchanges'] = {
                    'status': 'FAIL',
                    'message': 'No exchanges connected',
                    'details': exchanges_status
                }
                self.results['errors'].append('Exchanges: No working connections')
            elif working < total:
                self.results['checks']['exchanges'] = {
                    'status': 'WARNING',
                    'message': f'{working}/{total} exchanges connected',
                    'details': exchanges_status
                }
                self.results['warnings'].append(f'Exchanges: Only {working}/{total} working')
            else:
                self.results['checks']['exchanges'] = {
                    'status': 'PASS',
                    'message': f'All {total} exchanges connected',
                    'details': exchanges_status
                }
        
        except Exception as e:
            self.results['checks']['exchanges'] = {
                'status': 'FAIL',
                'message': f'Error: {str(e)}'
            }
            self.results['errors'].append(f'Exchanges: {str(e)}')
    
    def check_database(self):
        """Check database and encryption"""
        LOG.info("Checking database...")
        
        try:
            from security.database_encryption import DatabaseEncryption
            
            enc = DatabaseEncryption()
            
            # Check encryption works
            if not enc.verify_encryption():
                self.results['checks']['database'] = {
                    'status': 'FAIL',
                    'message': 'Encryption verification failed'
                }
                self.results['errors'].append('Database: Encryption not working')
                return
            
            # Check stored keys
            exchanges = enc.list_exchanges()
            
            self.results['checks']['database'] = {
                'status': 'PASS',
                'message': f'Database OK, {len(exchanges)} exchanges configured',
                'exchanges': exchanges
            }
            
            if len(exchanges) == 0:
                self.results['warnings'].append('Database: No API keys stored')
        
        except Exception as e:
            self.results['checks']['database'] = {
                'status': 'FAIL',
                'message': f'Error: {str(e)}'
            }
            self.results['errors'].append(f'Database: {str(e)}')
    
    def check_security(self):
        """Check security modules"""
        LOG.info("Checking security modules...")
        
        try:
            from monitoring.circuit_breaker import get_circuit_breaker
            
            breaker = get_circuit_breaker()
            
            # Check if properly initialized
            self.results['checks']['security'] = {
                'status': 'PASS',
                'message': 'Security modules loaded',
                'circuit_breaker': {
                    'failure_threshold': breaker.failure_threshold,
                    'timeout': breaker.timeout
                }
            }
        
        except Exception as e:
            self.results['checks']['security'] = {
                'status': 'FAIL',
                'message': f'Error: {str(e)}'
            }
            self.results['errors'].append(f'Security: {str(e)}')
    
    def check_monitoring(self):
        """Check monitoring systems"""
        LOG.info("Checking monitoring...")
        
        try:
            from monitoring.exchange_health_monitor import ExchangeHealthMonitor
            
            monitor = ExchangeHealthMonitor()
            health = monitor.get_all_health()
            
            unhealthy = [ex for ex, status in health.items() if not status.get('is_healthy')]
            
            if unhealthy:
                self.results['checks']['monitoring'] = {
                    'status': 'WARNING',
                    'message': f'{len(unhealthy)} exchanges unhealthy',
                    'unhealthy': unhealthy
                }
                self.results['warnings'].append(f'Monitoring: {len(unhealthy)} exchanges down')
            else:
                self.results['checks']['monitoring'] = {
                    'status': 'PASS',
                    'message': 'All exchanges healthy',
                    'health': health
                }
        
        except Exception as e:
            self.results['checks']['monitoring'] = {
                'status': 'FAIL',
                'message': f'Error: {str(e)}'
            }
            self.results['errors'].append(f'Monitoring: {str(e)}')
    
    def check_logs(self):
        """Check logging system"""
        LOG.info("Checking logs...")
        
        log_dir = Path('logs')
        
        if not log_dir.exists():
            self.results['checks']['logs'] = {
                'status': 'FAIL',
                'message': 'Logs directory missing'
            }
            self.results['errors'].append('Logs: Directory not found')
            self.results['recommendations'].append('Create logs directory: mkdir logs')
            return
        
        # Check log files
        expected_logs = ['all.log', 'error.log']
        existing = [f for f in expected_logs if (log_dir / f).exists()]
        
        if len(existing) < len(expected_logs):
            self.results['checks']['logs'] = {
                'status': 'WARNING',
                'message': f'Only {len(existing)}/{len(expected_logs)} log files exist'
            }
            self.results['warnings'].append(f'Logs: Missing {len(expected_logs) - len(existing)} files')
        else:
            # Check log sizes
            total_size = sum((log_dir / f).stat().st_size for f in existing)
            
            self.results['checks']['logs'] = {
                'status': 'PASS',
                'message': 'Logging system operational',
                'files': existing,
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            }
    
    def check_dependencies(self):
        """Check Python dependencies"""
        LOG.info("Checking dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'pybit',
            'requests',
            'cryptography',
            'pandas'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            self.results['checks']['dependencies'] = {
                'status': 'FAIL',
                'message': f'Missing packages: {", ".join(missing)}'
            }
            self.results['errors'].append(f'Dependencies: {len(missing)} packages missing')
            self.results['recommendations'].append(f'Install: pip install {" ".join(missing)}')
        else:
            self.results['checks']['dependencies'] = {
                'status': 'PASS',
                'message': f'All {len(required_packages)} dependencies installed'
            }
    
    def _compute_overall_status(self):
        """Compute overall status from checks"""
        statuses = [check['status'] for check in self.results['checks'].values()]
        
        if 'FAIL' in statuses:
            self.results['overall_status'] = 'FAIL'
        elif 'WARNING' in statuses:
            self.results['overall_status'] = 'WARNING'
        else:
            self.results['overall_status'] = 'PASS'
    
    def print_report(self):
        """Print diagnostic report"""
        print("\n" + "=" * 60)
        print("🔍 SMARTORDER PRO - DIAGNOSTIC REPORT")
        print("=" * 60)
        print(f"\nTimestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self._get_status_emoji(self.results['overall_status'])} {self.results['overall_status']}")
        
        print("\n📋 Checks:")
        for name, check in self.results['checks'].items():
            emoji = self._get_status_emoji(check['status'])
            print(f"  {emoji} {name.capitalize()}: {check['message']}")
        
        if self.results['warnings']:
            print("\n⚠️ Warnings:")
            for warning in self.results['warnings']:
                print(f"  - {warning}")
        
        if self.results['errors']:
            print("\n❌ Errors:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        if self.results['recommendations']:
            print("\n💡 Recommendations:")
            for rec in self.results['recommendations']:
                print(f"  - {rec}")
        
        print("\n" + "=" * 60)
        
        # Summary
        total_checks = len(self.results['checks'])
        passed = sum(1 for c in self.results['checks'].values() if c['status'] == 'PASS')
        warnings = sum(1 for c in self.results['checks'].values() if c['status'] == 'WARNING')
        failed = sum(1 for c in self.results['checks'].values() if c['status'] == 'FAIL')
        
        print(f"\nSummary: {passed} passed, {warnings} warnings, {failed} failed (of {total_checks} total)")
        
        if self.results['overall_status'] == 'PASS':
            print("\n✅ Bot is READY for production!")
        elif self.results['overall_status'] == 'WARNING':
            print("\n⚠️ Bot has warnings - review before production")
        else:
            print("\n❌ Bot has critical errors - FIX before production")
        
        print("=" * 60 + "\n")
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        return {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌',
            'UNKNOWN': '❓'
        }.get(status, '❓')
    
    def save_report(self, filepath: str = 'diagnostic_report.json'):
        """Save diagnostic report to JSON"""
        import json
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        LOG.info(f"Report saved to {filepath}")


def main():
    """Run diagnostic"""
    diagnostic = BotDiagnostic()
    diagnostic.run_all_checks()
    diagnostic.print_report()
    diagnostic.save_report()
    
    # Exit code based on status
    if diagnostic.results['overall_status'] == 'FAIL':
        sys.exit(1)
    elif diagnostic.results['overall_status'] == 'WARNING':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
