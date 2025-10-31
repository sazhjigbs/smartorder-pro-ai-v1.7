#!/usr/bin/env python3
"""
🔍 BOT DIAGNOSTIC PRO - SmartOrder PRO
=====================================
by MAIGA ABOUBACAR

Analyse automatique complète:
- Modules Python (imports, syntax, dépendances)
- Services systemd (status, logs, crashes)
- APIs (endpoints, réponses, erreurs)
- Fichiers dupliqués
- Configuration cohérence
- Performance & anomalies
- Génère rapport détaillé avec solutions

Usage:
    python3 bot_diagnostic_pro.py
    python3 bot_diagnostic_pro.py --fix-auto  # Applique corrections auto
"""

import os
import sys
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re

@dataclass
class DiagnosticResult:
    """Résultat d'un diagnostic"""
    category: str
    item: str
    status: str  # OK, WARNING, ERROR, CRITICAL
    message: str
    solution: Optional[str] = None
    auto_fixable: bool = False

class BotDiagnosticPro:
    """Diagnostic professionnel complet du bot"""
    
    def __init__(self, bot_path: str = "/opt/smartorder-pro"):
        self.bot_path = Path(bot_path)
        self.results: List[DiagnosticResult] = []
        self.errors_count = 0
        self.warnings_count = 0
        self.duplicates: Dict[str, List[str]] = {}
        
    def run_full_diagnostic(self) -> Dict:
        """Lance diagnostic complet"""
        print("🔍 SmartOrder PRO - Diagnostic Complet")
        print("=" * 60)
        print(f"📁 Path: {self.bot_path}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # 1. Structure fichiers
        print("📂 [1/8] Analyse structure fichiers...")
        self._check_file_structure()
        
        # 2. Modules Python
        print("🐍 [2/8] Test modules Python...")
        self._check_python_modules()
        
        # 3. Fichiers dupliqués
        print("🔄 [3/8] Détection doublons...")
        self._detect_duplicates()
        
        # 4. Services systemd
        print("⚙️  [4/8] Vérification services...")
        self._check_systemd_services()
        
        # 5. APIs endpoints
        print("📡 [5/8] Test APIs...")
        self._check_apis()
        
        # 6. Configuration
        print("⚙️  [6/8] Validation configuration...")
        self._check_configuration()
        
        # 7. Logs & Crashes
        print("📜 [7/8] Analyse logs & crashes...")
        self._analyze_logs()
        
        # 8. Performance
        print("⚡ [8/8] Check performance...")
        self._check_performance()
        
        # Génère rapport
        return self._generate_report()
    
    def _check_file_structure(self):
        """Vérifie structure fichiers essentiels"""
        essential_files = {
            "core/adaptive_scalping_engine.py": "Module Adaptive Scalping",
            "core/smart_position_manager.py": "Module Position Manager",
            "core/multi_tp_and_funding_optimizer.py": "Module Multi-TP & Funding",
            "smart_strategy_manager.py": "Smart Strategy Manager",
            "api/main.py": "API Principale",
            "run_paper_infinity_pro.py": "Script Paper Trading",
            "strategies_config_complete.json": "Config Stratégies",
        }
        
        for file_path, description in essential_files.items():
            full_path = self.bot_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                if size > 100:  # Au moins 100 bytes
                    self.results.append(DiagnosticResult(
                        category="STRUCTURE",
                        item=file_path,
                        status="OK",
                        message=f"{description} présent ({size} bytes)"
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        category="STRUCTURE",
                        item=file_path,
                        status="WARNING",
                        message=f"{description} trop petit ({size} bytes)",
                        solution="Vérifier contenu du fichier"
                    ))
                    self.warnings_count += 1
            else:
                self.results.append(DiagnosticResult(
                    category="STRUCTURE",
                    item=file_path,
                    status="ERROR",
                    message=f"{description} MANQUANT",
                    solution=f"Créer/restaurer {file_path}"
                ))
                self.errors_count += 1
    
    def _check_python_modules(self):
        """Test imports modules Python"""
        modules_to_test = [
            ("core.adaptive_scalping_engine", "AdaptiveScalpingEngine"),
            ("core.smart_position_manager", "SmartPositionManager"),
            ("core.multi_tp_and_funding_optimizer", "MultiTPFundingOptimizer"),
        ]
        
        for module_path, class_name in modules_to_test:
            try:
                # Change to bot directory
                sys.path.insert(0, str(self.bot_path))
                
                # Try import
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name, None)
                
                if cls:
                    self.results.append(DiagnosticResult(
                        category="PYTHON",
                        item=f"{module_path}.{class_name}",
                        status="OK",
                        message="Import successful"
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        category="PYTHON",
                        item=f"{module_path}.{class_name}",
                        status="WARNING",
                        message=f"Class {class_name} not found in module",
                        solution="Vérifier nom de classe"
                    ))
                    self.warnings_count += 1
                    
            except ImportError as e:
                self.results.append(DiagnosticResult(
                    category="PYTHON",
                    item=f"{module_path}.{class_name}",
                    status="ERROR",
                    message=f"Import failed: {str(e)}",
                    solution="Vérifier dépendances et syntax Python"
                ))
                self.errors_count += 1
            except Exception as e:
                self.results.append(DiagnosticResult(
                    category="PYTHON",
                    item=f"{module_path}.{class_name}",
                    status="ERROR",
                    message=f"Error: {str(e)}",
                    solution="Vérifier code du module"
                ))
                self.errors_count += 1
    
    def _detect_duplicates(self):
        """Détecte fichiers dupliqués par hash MD5"""
        file_hashes: Dict[str, List[str]] = {}
        
        # Scan tous les fichiers Python et HTML
        for ext in ["*.py", "*.html", "*.json"]:
            for file_path in self.bot_path.rglob(ext):
                # Ignore venv et backups
                if "venv" in str(file_path) or "backup" in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        
                    if file_hash not in file_hashes:
                        file_hashes[file_hash] = []
                    file_hashes[file_hash].append(str(file_path))
                except:
                    pass
        
        # Identifie doublons
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                self.duplicates[file_hash] = paths
                self.results.append(DiagnosticResult(
                    category="DUPLICATES",
                    item=f"{len(paths)} fichiers identiques",
                    status="WARNING",
                    message=f"Doublons: {', '.join([Path(p).name for p in paths])}",
                    solution="Supprimer fichiers en double, garder 1 seul",
                    auto_fixable=True
                ))
                self.warnings_count += 1
        
        if not self.duplicates:
            self.results.append(DiagnosticResult(
                category="DUPLICATES",
                item="Scan complet",
                status="OK",
                message="Aucun doublon détecté"
            ))
    
    def _check_systemd_services(self):
        """Vérifie status services systemd"""
        try:
            # List all smartorder services
            result = subprocess.run(
                ["systemctl", "list-units", "smartorder*", "--all", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.split('\n')
            
            running_services = []
            failed_services = []
            inactive_services = []
            
            for line in lines:
                if 'smartorder' in line.lower():
                    if 'running' in line:
                        service_name = line.split()[0]
                        running_services.append(service_name)
                    elif 'failed' in line:
                        service_name = line.split()[0]
                        failed_services.append(service_name)
                    elif 'inactive' in line or 'dead' in line:
                        service_name = line.split()[0]
                        inactive_services.append(service_name)
            
            # Report running
            for svc in running_services:
                self.results.append(DiagnosticResult(
                    category="SERVICES",
                    item=svc,
                    status="OK",
                    message="Service running"
                ))
            
            # Report failed
            for svc in failed_services:
                self.results.append(DiagnosticResult(
                    category="SERVICES",
                    item=svc,
                    status="CRITICAL",
                    message="Service FAILED",
                    solution=f"journalctl -u {svc} --no-pager -n 50"
                ))
                self.errors_count += 1
            
            # Check if critical services are running
            critical_services = ["smartorder-api.service", "smartorder-papertrading.service"]
            for svc in critical_services:
                if svc not in running_services:
                    self.results.append(DiagnosticResult(
                        category="SERVICES",
                        item=svc,
                        status="CRITICAL",
                        message="Service critique non actif",
                        solution=f"systemctl start {svc}"
                    ))
                    self.errors_count += 1
                    
        except Exception as e:
            self.results.append(DiagnosticResult(
                category="SERVICES",
                item="systemctl",
                status="ERROR",
                message=f"Cannot check services: {str(e)}",
                solution="Vérifier permissions systemctl"
            ))
            self.errors_count += 1
    
    def _check_apis(self):
        """Test endpoints API"""
        api_endpoints = [
            ("http://localhost:8000/api/status", "Status API"),
            ("http://localhost:8000/api/pnl", "PnL API"),
            ("http://localhost:8000/api/strategies", "Strategies API"),
            ("http://localhost:8000/api/positions", "Positions API"),
            ("http://localhost:8000/api/stats", "Stats API"),
        ]
        
        try:
            import requests
            
            for url, name in api_endpoints:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        self.results.append(DiagnosticResult(
                            category="API",
                            item=name,
                            status="OK",
                            message=f"Endpoint responds (HTTP {response.status_code})"
                        ))
                    else:
                        self.results.append(DiagnosticResult(
                            category="API",
                            item=name,
                            status="WARNING",
                            message=f"Endpoint returns HTTP {response.status_code}",
                            solution="Vérifier API handler"
                        ))
                        self.warnings_count += 1
                except requests.exceptions.RequestException as e:
                    self.results.append(DiagnosticResult(
                        category="API",
                        item=name,
                        status="ERROR",
                        message=f"Cannot reach endpoint: {str(e)}",
                        solution="Vérifier que smartorder-api.service est actif"
                    ))
                    self.errors_count += 1
        except ImportError:
            self.results.append(DiagnosticResult(
                category="API",
                item="requests library",
                status="WARNING",
                message="Cannot test APIs (requests not installed)",
                solution="pip install requests"
            ))
            self.warnings_count += 1
    
    def _check_configuration(self):
        """Valide fichiers de configuration"""
        config_files = [
            "strategies_config_complete.json",
            "config/trading_config.json",
        ]
        
        for config_file in config_files:
            full_path = self.bot_path / config_file
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                    
                    self.results.append(DiagnosticResult(
                        category="CONFIG",
                        item=config_file,
                        status="OK",
                        message=f"Valid JSON ({len(data)} keys)"
                    ))
                except json.JSONDecodeError as e:
                    self.results.append(DiagnosticResult(
                        category="CONFIG",
                        item=config_file,
                        status="CRITICAL",
                        message=f"Invalid JSON: {str(e)}",
                        solution="Corriger syntaxe JSON"
                    ))
                    self.errors_count += 1
            else:
                self.results.append(DiagnosticResult(
                    category="CONFIG",
                    item=config_file,
                    status="WARNING",
                    message="Config file not found",
                    solution=f"Créer {config_file}"
                ))
                self.warnings_count += 1
    
    def _analyze_logs(self):
        """Analyse logs pour détecter crashes et erreurs"""
        log_files = [
            "logs/paper_trading.log",
            "logs/api.log",
            "logs/smartorder.log",
        ]
        
        error_patterns = [
            r"ERROR",
            r"CRITICAL",
            r"Exception",
            r"Traceback",
            r"Failed",
            r"Crash",
        ]
        
        for log_file in log_files:
            full_path = self.bot_path / log_file
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        # Read last 1000 lines
                        lines = f.readlines()[-1000:]
                    
                    errors_found = 0
                    for line in lines:
                        for pattern in error_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                errors_found += 1
                                break
                    
                    if errors_found == 0:
                        self.results.append(DiagnosticResult(
                            category="LOGS",
                            item=log_file,
                            status="OK",
                            message="No errors in recent logs"
                        ))
                    elif errors_found < 10:
                        self.results.append(DiagnosticResult(
                            category="LOGS",
                            item=log_file,
                            status="WARNING",
                            message=f"{errors_found} errors found in recent logs",
                            solution=f"tail -100 {full_path}"
                        ))
                        self.warnings_count += 1
                    else:
                        self.results.append(DiagnosticResult(
                            category="LOGS",
                            item=log_file,
                            status="ERROR",
                            message=f"{errors_found} errors found in recent logs",
                            solution=f"grep -E 'ERROR|CRITICAL' {full_path} | tail -20"
                        ))
                        self.errors_count += 1
                        
                except Exception as e:
                    self.results.append(DiagnosticResult(
                        category="LOGS",
                        item=log_file,
                        status="WARNING",
                        message=f"Cannot read log: {str(e)}"
                    ))
                    self.warnings_count += 1
    
    def _check_performance(self):
        """Check performance et ressources"""
        try:
            # Check disk space
            result = subprocess.run(
                ["df", "-h", str(self.bot_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse disk usage
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                usage_line = lines[1]
                parts = usage_line.split()
                if len(parts) >= 5:
                    usage_percent = int(parts[4].replace('%', ''))
                    
                    if usage_percent < 80:
                        self.results.append(DiagnosticResult(
                            category="PERFORMANCE",
                            item="Disk Space",
                            status="OK",
                            message=f"Disk usage: {usage_percent}%"
                        ))
                    elif usage_percent < 90:
                        self.results.append(DiagnosticResult(
                            category="PERFORMANCE",
                            item="Disk Space",
                            status="WARNING",
                            message=f"Disk usage: {usage_percent}% (attention)",
                            solution="Nettoyer logs et fichiers inutiles"
                        ))
                        self.warnings_count += 1
                    else:
                        self.results.append(DiagnosticResult(
                            category="PERFORMANCE",
                            item="Disk Space",
                            status="CRITICAL",
                            message=f"Disk usage: {usage_percent}% (CRITIQUE)",
                            solution="Libérer espace disque immédiatement"
                        ))
                        self.errors_count += 1
        except:
            pass
    
    def _generate_report(self) -> Dict:
        """Génère rapport final"""
        print()
        print("=" * 60)
        print("📊 RÉSULTAT DU DIAGNOSTIC")
        print("=" * 60)
        print()
        
        # Count by status
        ok_count = sum(1 for r in self.results if r.status == "OK")
        warning_count = sum(1 for r in self.results if r.status == "WARNING")
        error_count = sum(1 for r in self.results if r.status == "ERROR")
        critical_count = sum(1 for r in self.results if r.status == "CRITICAL")
        
        print(f"✅ OK:       {ok_count}")
        print(f"⚠️  WARNING:  {warning_count}")
        print(f"❌ ERROR:    {error_count}")
        print(f"🔥 CRITICAL: {critical_count}")
        print()
        
        # Group by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result)
        
        # Print by category
        for category, results in sorted(by_category.items()):
            print(f"\n{'='*60}")
            print(f"📂 {category}")
            print(f"{'='*60}")
            
            for result in results:
                icon = {
                    "OK": "✅",
                    "WARNING": "⚠️ ",
                    "ERROR": "❌",
                    "CRITICAL": "🔥"
                }.get(result.status, "ℹ️")
                
                print(f"{icon} {result.item}")
                print(f"   {result.message}")
                if result.solution:
                    print(f"   💡 Solution: {result.solution}")
                print()
        
        # Duplicates detail
        if self.duplicates:
            print(f"\n{'='*60}")
            print("🔄 FICHIERS DUPLIQUÉS DÉTAILS")
            print(f"{'='*60}")
            for hash_val, paths in self.duplicates.items():
                print(f"\n📄 {len(paths)} fichiers identiques:")
                for path in paths:
                    print(f"   - {path}")
        
        # Save report to file
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "ok": ok_count,
                "warnings": warning_count,
                "errors": error_count,
                "critical": critical_count,
                "total": len(self.results)
            },
            "results": [asdict(r) for r in self.results],
            "duplicates": self.duplicates
        }
        
        report_file = Path("bot_diagnostic_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Rapport sauvegardé: {report_file}")
        print()
        
        # Global status
        if critical_count > 0:
            print("🔥 STATUS: CRITIQUE - Action immédiate requise")
            return_code = 2
        elif error_count > 0:
            print("❌ STATUS: ERREURS - Corrections nécessaires")
            return_code = 1
        elif warning_count > 0:
            print("⚠️  STATUS: WARNINGS - Améliorations recommandées")
            return_code = 0
        else:
            print("✅ STATUS: EXCELLENT - Système opérationnel")
            return_code = 0
        
        print("=" * 60)
        
        return {
            "report": report,
            "return_code": return_code
        }


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Bot Diagnostic PRO - Analyse complète SmartOrder PRO"
    )
    parser.add_argument(
        "--bot-path",
        default="/opt/smartorder-pro",
        help="Chemin vers le bot (défaut: /opt/smartorder-pro)"
    )
    parser.add_argument(
        "--fix-auto",
        action="store_true",
        help="Applique corrections automatiques"
    )
    
    args = parser.parse_args()
    
    diagnostic = BotDiagnosticPro(bot_path=args.bot_path)
    result = diagnostic.run_full_diagnostic()
    
    sys.exit(result["return_code"])


if __name__ == "__main__":
    main()
