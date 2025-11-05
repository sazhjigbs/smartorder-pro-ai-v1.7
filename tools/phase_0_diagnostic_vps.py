#!/usr/bin/env python3
"""
🔍 PHASE 0 - DIAGNOSTIC INITIAL VPS
SmartOrder PRO AI v2.4 - SAFELOGIC

Validation complète avant déploiement Phases 1-8
by MAIGA ABOUBAKR - SAFELOGIC
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

class Phase0Diagnostic:
    def __init__(self, base_path="/opt/smartorder-pro"):
        self.base_path = Path(base_path)
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "PHASE_0",
            "status": "IN_PROGRESS",
            "checks": {},
            "errors": [],
            "warnings": [],
            "critical_issues": []
        }
        self.success = True
    
    def check_python_version(self):
        """Vérifier version Python >= 3.10"""
        print("\n🔍 [1/8] Checking Python version...")
        
        import platform
        version = platform.python_version()
        major, minor = map(int, version.split('.')[:2])
        
        if major >= 3 and minor >= 10:
            print(f"   ✅ Python {version} (>= 3.10 required)")
            self.report["checks"]["python_version"] = {"status": "OK", "version": version}
        else:
            print(f"   ❌ Python {version} (3.10+ required)")
            self.report["checks"]["python_version"] = {"status": "FAIL", "version": version}
            self.report["critical_issues"].append(f"Python {version} < 3.10")
            self.success = False
    
    def check_dependencies(self):
        """Vérifier dépendances critiques"""
        print("\n🔍 [2/8] Checking critical dependencies...")
        
        critical_deps = {
            'ccxt': '4.2.4',
            'flask': None,
            'aiohttp': None,
            'websockets': None,
            'psutil': None,
            'pandas': None,
            'requests': None
        }
        
        deps_status = {}
        missing = []
        
        for dep, min_version in critical_deps.items():
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'unknown')
                
                if dep == 'ccxt' and min_version:
                    # Vérifier version ccxt
                    major, minor, patch = version.split('.')[:3]
                    if int(major) < 4 or (int(major) == 4 and int(minor) < 2):
                        print(f"   ⚠️  {dep} {version} (>= {min_version} recommended)")
                        self.report["warnings"].append(f"{dep} {version} < {min_version}")
                    else:
                        print(f"   ✅ {dep} {version}")
                else:
                    print(f"   ✅ {dep} {version}")
                
                deps_status[dep] = {"installed": True, "version": version}
            except ImportError:
                print(f"   ❌ {dep} NOT INSTALLED")
                deps_status[dep] = {"installed": False}
                missing.append(dep)
        
        self.report["checks"]["dependencies"] = deps_status
        
        if missing:
            self.report["critical_issues"].append(f"Missing dependencies: {', '.join(missing)}")
            self.success = False
    
    def check_ports(self):
        """Vérifier ports disponibles"""
        print("\n🔍 [3/8] Checking required ports...")
        
        required_ports = {
            "8555": "Portal Web Principal",
            "8091": "API Unifiée v2.4",
            "8181": "Dashboard God Mode v3.0",
            "8182": "WebSocket Live Data"
        }
        
        ports_status = {}
        
        try:
            result = subprocess.run(
                ["ss", "-tlnp"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for port, desc in required_ports.items():
                if f":{port}" in result.stdout:
                    print(f"   ⚠️  Port {port} ({desc}) - ALREADY IN USE")
                    ports_status[port] = {"available": False, "description": desc}
                    self.report["warnings"].append(f"Port {port} already in use")
                else:
                    print(f"   ✅ Port {port} ({desc}) - Available")
                    ports_status[port] = {"available": True, "description": desc}
            
            self.report["checks"]["ports"] = ports_status
            
        except Exception as e:
            print(f"   ❌ Error checking ports: {e}")
            self.report["errors"].append(f"Port check failed: {e}")
    
    def check_systemd_services(self):
        """Vérifier services systemd existants"""
        print("\n🔍 [4/8] Checking systemd services...")
        
        service_patterns = ["smartorder*", "bybit*", "safelogic*"]
        services_found = []
        
        try:
            for pattern in service_patterns:
                result = subprocess.run(
                    ["systemctl", "list-units", "--all", "--no-pager", pattern],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                for line in result.stdout.split('\n'):
                    if '.service' in line:
                        parts = line.split()
                        if parts:
                            service_name = parts[0]
                            status = parts[3] if len(parts) > 3 else 'unknown'
                            services_found.append({
                                "name": service_name,
                                "status": status
                            })
                            print(f"   📌 Found: {service_name} ({status})")
            
            self.report["checks"]["systemd_services"] = services_found
            
            if services_found:
                print(f"   ⚠️  {len(services_found)} existing services detected")
                self.report["warnings"].append(f"{len(services_found)} services will be reconfigured")
            else:
                print("   ✅ No conflicting services")
                
        except Exception as e:
            print(f"   ⚠️  Systemd check error: {e}")
            self.report["checks"]["systemd_services"] = {"error": str(e)}
    
    def check_directory_structure(self):
        """Vérifier structure des dossiers"""
        print("\n🔍 [5/8] Checking directory structure...")
        
        required_dirs = [
            "config",
            "core",
            "api",
            "logs",
            "strategies",
            "db",
            "guardian"
        ]
        
        dirs_status = {}
        
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            exists = dir_path.exists()
            
            if exists:
                print(f"   ✅ {dir_name}/ exists")
                dirs_status[dir_name] = {"exists": True, "path": str(dir_path)}
            else:
                print(f"   ⚠️  {dir_name}/ missing (will be created)")
                dirs_status[dir_name] = {"exists": False, "path": str(dir_path)}
        
        self.report["checks"]["directories"] = dirs_status
    
    def check_config_files(self):
        """Vérifier fichiers de configuration critiques"""
        print("\n🔍 [6/8] Checking configuration files...")
        
        config_files = [
            "config/exchanges.json",
            "config/bot_config.json",
            ".env"
        ]
        
        configs_status = {}
        
        for config in config_files:
            config_path = self.base_path / config
            
            if config_path.exists():
                size = config_path.stat().st_size
                print(f"   ✅ {config} ({size} bytes)")
                configs_status[config] = {
                    "exists": True,
                    "size": size,
                    "path": str(config_path)
                }
            else:
                print(f"   ⚠️  {config} missing")
                configs_status[config] = {"exists": False}
                self.report["warnings"].append(f"Config missing: {config}")
        
        self.report["checks"]["config_files"] = configs_status
    
    def check_disk_space(self):
        """Vérifier espace disque disponible"""
        print("\n🔍 [7/8] Checking disk space...")
        
        try:
            result = subprocess.run(
                ["df", "-h", str(self.base_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                total = parts[1]
                used = parts[2]
                available = parts[3]
                percent = parts[4]
                
                print(f"   📊 Total: {total}, Used: {used}, Available: {available} ({percent})")
                
                self.report["checks"]["disk_space"] = {
                    "total": total,
                    "used": used,
                    "available": available,
                    "percent": percent
                }
                
                # Vérifier si au moins 5GB disponible
                avail_gb = float(available.replace('G', '').replace('M', '0.'))
                if avail_gb < 5:
                    print(f"   ⚠️  Low disk space: {available}")
                    self.report["warnings"].append(f"Low disk space: {available}")
                else:
                    print(f"   ✅ Sufficient disk space")
                    
        except Exception as e:
            print(f"   ⚠️  Disk check error: {e}")
            self.report["errors"].append(f"Disk check failed: {e}")
    
    def check_network_connectivity(self):
        """Vérifier connectivité réseau vers exchanges"""
        print("\n🔍 [8/8] Checking network connectivity...")
        
        exchanges_api = {
            "bybit": "https://api.bybit.com/v5/market/time",
            "binance": "https://api.binance.com/api/v3/time",
            "okx": "https://www.okx.com/api/v5/public/time"
        }
        
        connectivity = {}
        
        for exchange, url in exchanges_api.items():
            try:
                import requests
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ {exchange.upper()} API reachable")
                    connectivity[exchange] = {"reachable": True, "status_code": 200}
                else:
                    print(f"   ⚠️  {exchange.upper()} API responded with {response.status_code}")
                    connectivity[exchange] = {"reachable": False, "status_code": response.status_code}
            except Exception as e:
                print(f"   ❌ {exchange.upper()} API unreachable: {e}")
                connectivity[exchange] = {"reachable": False, "error": str(e)}
        
        self.report["checks"]["network_connectivity"] = connectivity
    
    def generate_report(self):
        """Générer rapport final"""
        print("\n" + "="*70)
        print("📊 PHASE 0 - DIAGNOSTIC REPORT")
        print("="*70)
        
        # Déterminer status final
        if self.success and not self.report["critical_issues"]:
            self.report["status"] = "SUCCESS"
            status_emoji = "✅"
            status_text = "READY FOR DEPLOYMENT"
        else:
            self.report["status"] = "FAILED"
            status_emoji = "❌"
            status_text = "DEPLOYMENT BLOCKED"
        
        print(f"\n{status_emoji} Status: {status_text}")
        print(f"📅 Timestamp: {self.report['timestamp']}")
        print(f"⚠️  Critical Issues: {len(self.report['critical_issues'])}")
        print(f"⚡ Warnings: {len(self.report['warnings'])}")
        print(f"❌ Errors: {len(self.report['errors'])}")
        
        if self.report["critical_issues"]:
            print(f"\n🚫 CRITICAL ISSUES:")
            for issue in self.report["critical_issues"]:
                print(f"   • {issue}")
        
        if self.report["warnings"]:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.report["warnings"][:5]:  # Limite à 5
                print(f"   • {warning}")
        
        # Sauvegarder rapport JSON
        logs_dir = self.base_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        report_json = logs_dir / "PHASE_0_REPORT.json"
        with open(report_json, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Full report: {report_json}")
        
        # Créer fichier SUCCESS ou FAILED
        if self.report["status"] == "SUCCESS":
            success_file = logs_dir / "PHASE_0_SUCCESS.log"
            with open(success_file, 'w') as f:
                f.write(f"PHASE 0 - SUCCESS\n")
                f.write(f"Timestamp: {self.report['timestamp']}\n")
                f.write(f"Ready for Phases 1-8 deployment\n")
            print(f"✅ Success marker: {success_file}")
            print("\n🚀 READY TO PROCEED WITH PHASES 1-8")
        else:
            failed_file = logs_dir / "PHASE_0_FAILED.log"
            with open(failed_file, 'w') as f:
                f.write(f"PHASE 0 - FAILED\n")
                f.write(f"Timestamp: {self.report['timestamp']}\n")
                f.write(f"Critical issues:\n")
                for issue in self.report["critical_issues"]:
                    f.write(f"  - {issue}\n")
            print(f"❌ Failed marker: {failed_file}")
            print("\n🛑 RESOLVE CRITICAL ISSUES BEFORE DEPLOYMENT")
        
        print("="*70)
        
        return self.report["status"] == "SUCCESS"

def main():
    parser = argparse.ArgumentParser(description='Phase 0 Diagnostic - SmartOrder PRO AI v2.4')
    parser.add_argument('--full', action='store_true', help='Run full diagnostic')
    parser.add_argument('--path', default='/opt/smartorder-pro', help='Base path')
    args = parser.parse_args()
    
    print("🔍 PHASE 0 - DIAGNOSTIC INITIAL")
    print("SmartOrder PRO AI v2.4 - SAFELOGIC")
    print("by MAIGA ABOUBAKR\n")
    
    diagnostic = Phase0Diagnostic(args.path)
    
    # Exécuter tous les checks
    diagnostic.check_python_version()
    diagnostic.check_dependencies()
    diagnostic.check_ports()
    diagnostic.check_systemd_services()
    diagnostic.check_directory_structure()
    diagnostic.check_config_files()
    diagnostic.check_disk_space()
    diagnostic.check_network_connectivity()
    
    # Générer rapport
    success = diagnostic.generate_report()
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
