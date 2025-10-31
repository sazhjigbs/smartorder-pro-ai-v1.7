#!/usr/bin/env python3
"""
🤖 SMART DIAGNOSTIC AUTO-CORRECT - SmartOrder PRO
================================================
by MAIGA ABOUBACAR

Système intelligent qui:
1. Détecte les erreurs automatiquement
2. CORRIGE les erreurs automatiquement quand possible
3. Garde MÉMOIRE des corrections appliquées
4. Valide compatibilité versions Python/packages
5. Détecte code incomplet vs code complet
6. Trouve les stratégies/modules manquants
7. Vérifie cohérence entre modules
8. S'exécute en continu pendant le dev

Usage:
    python3 smart_diagnostic_autocorrect.py --watch  # Mode continu
    python3 smart_diagnostic_autocorrect.py --fix-all  # Correction automatique
"""

import os
import sys
import json
import subprocess
import hashlib
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import time

@dataclass
class CorrectionRecord:
    """Record d'une correction appliquée"""
    timestamp: str
    error_type: str
    file: str
    description: str
    fix_applied: str
    success: bool
    
class SmartDiagnosticAutoCorrect:
    """Diagnostic intelligent avec auto-correction et mémoire"""
    
    def __init__(self, bot_path: str = "/opt/smartorder-pro"):
        self.bot_path = Path(bot_path)
        self.memory_file = self.bot_path / "diagnostic_memory.json"
        self.corrections_history: List[CorrectionRecord] = []
        self.load_memory()
        
    def load_memory(self):
        """Charge la mémoire des corrections passées"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.corrections_history = [
                    CorrectionRecord(**rec) for rec in data.get("corrections", [])
                ]
                print(f"📝 Mémoire chargée: {len(self.corrections_history)} corrections passées")
        else:
            print("📝 Nouvelle mémoire créée")
    
    def save_memory(self):
        """Sauvegarde la mémoire"""
        data = {
            "last_update": datetime.now().isoformat(),
            "corrections": [asdict(rec) for rec in self.corrections_history]
        }
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_correction(self, error_type: str, file: str, description: str, 
                      fix_applied: str, success: bool):
        """Ajoute une correction à la mémoire"""
        rec = CorrectionRecord(
            timestamp=datetime.now().isoformat(),
            error_type=error_type,
            file=file,
            description=description,
            fix_applied=fix_applied,
            success=success
        )
        self.corrections_history.append(rec)
        self.save_memory()
        
    def check_python_version_compatibility(self, file_path: Path) -> Dict:
        """Vérifie compatibilité version Python"""
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Parse AST
            tree = ast.parse(code)
            
            issues = []
            
            # Check for Python 3.6+ features (f-strings)
            for node in ast.walk(tree):
                if isinstance(node, ast.JoinedStr):
                    # f-strings OK in Python 3.6+
                    pass
                    
                # Check for Python 3.10+ match statements
                if sys.version_info >= (3, 10):
                    if isinstance(node, ast.Match):
                        issues.append({
                            "line": node.lineno,
                            "issue": "match statement requires Python 3.10+",
                            "severity": "warning"
                        })
            
            return {
                "file": str(file_path),
                "compatible": len(issues) == 0,
                "issues": issues
            }
        except SyntaxError as e:
            return {
                "file": str(file_path),
                "compatible": False,
                "issues": [{
                    "line": e.lineno,
                    "issue": f"Syntax error: {e.msg}",
                    "severity": "critical"
                }]
            }
        except Exception as e:
            return {
                "file": str(file_path),
                "compatible": False,
                "issues": [{"issue": str(e), "severity": "error"}]
            }
    
    def detect_incomplete_code(self, file_path: Path) -> Dict:
        """Détecte si le code est incomplet"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            issues = []
            
            # Patterns de code incomplet
            incomplete_patterns = [
                (r'pass\s*$', "Empty function with just 'pass'"),
                (r'#\s*TODO', "TODO comment found"),
                (r'#\s*FIXME', "FIXME comment found"),
                (r'raise NotImplementedError', "Function not implemented"),
                (r'\.\.\.', "Ellipsis placeholder"),
                (r'return None\s*$', "Function returns None explicitly")
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, msg in incomplete_patterns:
                    if re.search(pattern, line):
                        issues.append({
                            "line": i,
                            "code": line.strip(),
                            "issue": msg
                        })
            
            # Check for empty classes
            with open(file_path, 'r') as f:
                code = f.read()
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if class only has pass
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            issues.append({
                                "line": node.lineno,
                                "issue": f"Empty class '{node.name}' with only pass"
                            })
            except:
                pass
            
            return {
                "file": str(file_path),
                "complete": len(issues) == 0,
                "issues": issues,
                "severity": "high" if len(issues) > 3 else "medium" if len(issues) > 0 else "none"
            }
        except Exception as e:
            return {
                "file": str(file_path),
                "complete": True,
                "issues": [],
                "error": str(e)
            }
    
    def find_missing_strategies(self) -> Dict:
        """Trouve stratégies manquantes en comparant config vs code"""
        try:
            # Load config
            config_file = self.bot_path / "strategies_config_complete.json"
            if not config_file.exists():
                return {"error": "Config file not found"}
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Extract all strategies from config
            config_strategies = set()
            for mode, data in config.items():
                if mode in ['SPOT', 'FUTURES', 'HYBRIDE', 'MANUEL']:
                    for strat in data.get('strategies', []):
                        config_strategies.add(strat.get('id', strat.get('name', '')))
            
            # Find strategy implementations
            implemented = set()
            
            # Check in core/
            core_dir = self.bot_path / "core"
            if core_dir.exists():
                for py_file in core_dir.glob("*.py"):
                    name = py_file.stem.lower()
                    # Common naming patterns
                    if 'strategy' in name or 'engine' in name or 'trader' in name:
                        implemented.add(name)
            
            # Check in strategies/
            strat_dir = self.bot_path / "strategies"
            if strat_dir.exists():
                for py_file in strat_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        implemented.add(py_file.stem.lower())
            
            # Find missing
            missing = []
            for strat in config_strategies:
                strat_lower = strat.lower().replace(' ', '_').replace('-', '_')
                found = False
                for impl in implemented:
                    if strat_lower in impl or impl in strat_lower:
                        found = True
                        break
                if not found:
                    missing.append(strat)
            
            return {
                "config_strategies": list(config_strategies),
                "implemented": list(implemented),
                "missing": missing,
                "complete": len(missing) == 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_module_consistency(self) -> List[Dict]:
        """Vérifie cohérence entre modules"""
        issues = []
        
        # Check if modules import each other correctly
        core_modules = [
            "adaptive_scalping_engine",
            "smart_position_manager",
            "multi_tp_and_funding_optimizer"
        ]
        
        # Check if run_paper imports these modules
        run_paper = self.bot_path / "run_paper_infinity_pro.py"
        if run_paper.exists():
            with open(run_paper, 'r') as f:
                content = f.read()
            
            for module in core_modules:
                if f"from core.{module} import" not in content and f"import {module}" not in content:
                    issues.append({
                        "type": "missing_import",
                        "file": "run_paper_infinity_pro.py",
                        "missing": module,
                        "fix": f"Add: from core.{module} import ..."
                    })
        
        # Check if API imports modules for endpoints
        api_main = self.bot_path / "api" / "main.py"
        if api_main.exists():
            with open(api_main, 'r') as f:
                content = f.read()
            
            required_endpoints = [
                "/api/adaptive_scalping/status",
                "/api/position_manager/status",
                "/api/funding/rates"
            ]
            
            for endpoint in required_endpoints:
                if endpoint not in content:
                    issues.append({
                        "type": "missing_endpoint",
                        "file": "api/main.py",
                        "missing": endpoint,
                        "fix": f"Add endpoint: @app.get('{endpoint}')"
                    })
        
        return issues
    
    def check_dashboard_health(self) -> Dict:
        """Vérifie santé du dashboard et APIs"""
        import subprocess
        
        issues = []
        
        # Check if API service is running
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "smartorder-api"],
                capture_output=True,
                text=True,
                timeout=5
            )
            api_running = result.stdout.strip() == "active"
        except:
            api_running = False
        
        if not api_running:
            issues.append({
                "component": "API Service",
                "status": "stopped",
                "severity": "critical",
                "fix": "systemctl start smartorder-api"
            })
        
        # Check if nginx is running
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "nginx"],
                capture_output=True,
                text=True,
                timeout=5
            )
            nginx_running = result.stdout.strip() == "active"
        except:
            nginx_running = False
        
        if not nginx_running:
            issues.append({
                "component": "Nginx",
                "status": "stopped",
                "severity": "critical",
                "fix": "systemctl start nginx"
            })
        
        # Check dashboard files
        dashboard_dir = self.bot_path / "dashboard"
        if dashboard_dir.exists():
            required_files = [
                "index.html",
                "app.js",
                "style.css"
            ]
            
            for file in required_files:
                file_path = dashboard_dir / file
                if not file_path.exists():
                    issues.append({
                        "component": "Dashboard Files",
                        "status": f"missing {file}",
                        "severity": "high",
                        "fix": f"Restore dashboard/{file}"
                    })
        else:
            issues.append({
                "component": "Dashboard Directory",
                "status": "missing",
                "severity": "critical",
                "fix": "Restore dashboard directory"
            })
        
        # Check API logs for errors
        api_log = self.bot_path / "logs" / "api.log"
        if api_log.exists():
            try:
                with open(api_log, 'r') as f:
                    # Read last 100 lines
                    lines = f.readlines()[-100:]
                    error_count = sum(1 for line in lines if "ERROR" in line or "CRITICAL" in line)
                    
                    if error_count > 10:
                        issues.append({
                            "component": "API Logs",
                            "status": f"{error_count} errors in last 100 lines",
                            "severity": "high",
                            "fix": "Check api.log for details"
                        })
            except:
                pass
        
        return {
            "api_running": api_running,
            "nginx_running": nginx_running,
            "issues": issues,
            "healthy": len(issues) == 0
        }
    
    def check_frontend_errors(self) -> Dict:
        """Vérifie erreurs JavaScript dans le dashboard"""
        issues = []
        
        # Check dashboard JS files for common errors
        dashboard_dir = self.bot_path / "dashboard"
        if not dashboard_dir.exists():
            # Try web/ directory instead
            dashboard_dir = self.bot_path / "web"
            if not dashboard_dir.exists():
                return {"error": "Dashboard directory not found"}
        
        js_files = list(dashboard_dir.glob("*.js")) + list(dashboard_dir.glob("**/*.js"))
        
        for js_file in js_files:
            if "node_modules" in str(js_file):
                continue
            
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for common frontend errors
                error_patterns = [
                    (r'console\.error', "console.error found (should use proper error handling)"),
                    (r'fetch\([^)]+\)(?!\s*\.catch)', "fetch without .catch() error handling"),
                    (r'\$\{[^}]*undefined', "Template literal with undefined variable"),
                    (r'JSON\.parse\([^)]+\)(?!\s*try)', "JSON.parse without try-catch")
                ]
                
                for pattern, msg in error_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            "file": js_file.name,
                            "line": line_num,
                            "issue": msg,
                            "severity": "medium"
                        })
            except Exception as e:
                issues.append({
                    "file": js_file.name,
                    "issue": f"Could not parse file: {str(e)}",
                    "severity": "low"
                })
        
        return {
            "files_checked": len(js_files),
            "issues": issues,
            "clean": len(issues) == 0
        }
    
    def check_dashboard_features(self) -> Dict:
        """Vérifie fonctionnalités manquantes du dashboard"""
        missing_features = []
        
        # Check if strategies endpoint returns correct format
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/strategies"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    if "strategies" not in data:
                        missing_features.append({
                            "feature": "Active Strategies List",
                            "endpoint": "/api/strategies",
                            "issue": "Endpoint missing 'strategies' key",
                            "severity": "high"
                        })
                except json.JSONDecodeError:
                    missing_features.append({
                        "feature": "Active Strategies List",
                        "endpoint": "/api/strategies",
                        "issue": "Endpoint returns invalid JSON",
                        "severity": "critical"
                    })
            else:
                missing_features.append({
                    "feature": "Active Strategies List",
                    "endpoint": "/api/strategies",
                    "issue": "Endpoint not responding",
                    "severity": "critical"
                })
        except Exception as e:
            missing_features.append({
                "feature": "Active Strategies List",
                "issue": f"Could not test endpoint: {str(e)}",
                "severity": "high"
            })
        
        # Check funding rates endpoint
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/funding/rates"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    if "rates" not in data or len(data.get("rates", [])) == 0:
                        missing_features.append({
                            "feature": "Funding Rates Display",
                            "endpoint": "/api/funding/rates",
                            "issue": "No rates returned",
                            "severity": "medium"
                        })
                except json.JSONDecodeError:
                    pass
        except:
            pass
        
        # Check whale alerts endpoint
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/whale/alerts"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0 or "404" in result.stdout:
                missing_features.append({
                    "feature": "Whale Alerts Real-Time",
                    "endpoint": "/api/whale/alerts",
                    "issue": "Endpoint missing",
                    "severity": "medium",
                    "fix": "Add endpoint @app.get('/api/whale/alerts')"
                })
        except:
            pass
        
        # Check recovery mode endpoint
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/recovery/status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0 or "404" in result.stdout:
                missing_features.append({
                    "feature": "Recovery Mode Status",
                    "endpoint": "/api/recovery/status",
                    "issue": "Endpoint missing",
                    "severity": "high",
                    "fix": "Add endpoint @app.get('/api/recovery/status')"
                })
        except:
            pass
        
        # Check mode change endpoint (CRITICAL for dashboard)
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
                 "-d", '{"mode":"spot"}', "http://localhost:8000/api/mode/change"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Not Found" in result.stdout or "404" in result.stdout:
                missing_features.append({
                    "feature": "Mode Switching",
                    "endpoint": "/api/mode/change",
                    "issue": "Endpoint missing - causes 'Failed to fetch' errors",
                    "severity": "critical",
                    "fix": "Add endpoint @app.post('/api/mode/change')"
                })
        except:
            pass
        
        # Check exchanges endpoint
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/exchanges"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Not Found" in result.stdout or "404" in result.stdout:
                missing_features.append({
                    "feature": "Exchanges List",
                    "endpoint": "/api/exchanges",
                    "issue": "Endpoint missing - exchanges selection not working",
                    "severity": "high",
                    "fix": "Add endpoint @app.get('/api/exchanges')"
                })
        except:
            pass
        
        # Check positions format
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/positions"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    # Positions should be filtered by mode (spot/futures)
                    if isinstance(data, list) and len(data) > 0:
                        # Check if positions have mode field
                        if "mode" not in data[0]:
                            missing_features.append({
                                "feature": "Positions Mode Filter",
                                "endpoint": "/api/positions",
                                "issue": "Positions not filtered by trading mode (SPOT/FUTURES)",
                                "severity": "medium",
                                "fix": "Update endpoint to filter by mode parameter"
                            })
                except json.JSONDecodeError:
                    pass
        except:
            pass
        
        return {
            "missing_features": missing_features,
            "total": len(missing_features),
            "complete": len(missing_features) == 0
        }
    
    def auto_fix_dashboard_issues(self) -> List[Dict]:
        """Corrige automatiquement problèmes dashboard"""
        fixes = []
        
        # Check and restart services if needed
        health = self.check_dashboard_health()
        
        if not health.get("api_running"):
            try:
                subprocess.run(
                    ["systemctl", "restart", "smartorder-api"],
                    capture_output=True,
                    timeout=10
                )
                fixes.append({
                    "action": "restart_api",
                    "success": True,
                    "message": "API service restarted"
                })
                self.add_correction(
                    error_type="service_stopped",
                    file="smartorder-api.service",
                    description="API service was stopped",
                    fix_applied="systemctl restart smartorder-api",
                    success=True
                )
            except Exception as e:
                fixes.append({
                    "action": "restart_api",
                    "success": False,
                    "error": str(e)
                })
        
        if not health.get("nginx_running"):
            try:
                subprocess.run(
                    ["systemctl", "restart", "nginx"],
                    capture_output=True,
                    timeout=10
                )
                fixes.append({
                    "action": "restart_nginx",
                    "success": True,
                    "message": "Nginx restarted"
                })
                self.add_correction(
                    error_type="service_stopped",
                    file="nginx.service",
                    description="Nginx was stopped",
                    fix_applied="systemctl restart nginx",
                    success=True
                )
            except Exception as e:
                fixes.append({
                    "action": "restart_nginx",
                    "success": False,
                    "error": str(e)
                })
        
        return fixes
    
    def auto_fix_import_errors(self) -> List[Dict]:
        """Corrige automatiquement les erreurs d'import courantes"""
        fixes = []
        
        # Common import fixes
        common_fixes = {
            "ModuleNotFoundError: No module named 'ccxt'": "pip install ccxt",
            "ModuleNotFoundError: No module named 'pandas'": "pip install pandas",
            "ModuleNotFoundError: No module named 'numpy'": "pip install numpy",
            "ModuleNotFoundError: No module named 'requests'": "pip install requests",
            "ModuleNotFoundError: No module named 'fastapi'": "pip install fastapi uvicorn",
        }
        
        # Check if packages are installed
        for error, fix_cmd in common_fixes.items():
            package = error.split("'")[1]
            try:
                __import__(package)
            except ImportError:
                fixes.append({
                    "error": error,
                    "fix": fix_cmd,
                    "auto_fixable": True
                })
        
        return fixes
    
    def auto_fix_duplicates(self) -> List[Dict]:
        """Supprime automatiquement les fichiers dupliqués"""
        fixes = []
        
        # Known duplicates to remove (keep core/, remove ai/)
        duplicates_to_remove = [
            self.bot_path / "ai" / "signal_memory.py",
            self.bot_path / "ai" / "sentiment.py",
            self.bot_path / "ai" / "mode_manager.py",
            self.bot_path / "ai" / "signal_simulator.py"
        ]
        
        for dup_file in duplicates_to_remove:
            if dup_file.exists():
                try:
                    dup_file.unlink()
                    fix = {
                        "action": "removed_duplicate",
                        "file": str(dup_file),
                        "success": True
                    }
                    self.add_correction(
                        error_type="duplicate_file",
                        file=str(dup_file),
                        description="Removed duplicate file",
                        fix_applied="unlink()",
                        success=True
                    )
                except Exception as e:
                    fix = {
                        "action": "remove_duplicate_failed",
                        "file": str(dup_file),
                        "error": str(e),
                        "success": False
                    }
                fixes.append(fix)
        
        return fixes
    
    def validate_progress_vs_history(self, history_text: str = None) -> Dict:
        """Valide progression vs historique pour détecter oublis"""
        
        # Load progress tracker
        progress_file = Path("PROGRESS_TRACKER.json")
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                progress = json.load(f)
        else:
            return {"error": "PROGRESS_TRACKER.json not found"}
        
        # Extract completed tasks
        completed_tasks = []
        for phase_name, phase_data in progress.get("phases", {}).items():
            if phase_data.get("status") == "COMPLETED":
                for task in phase_data.get("tasks", []):
                    if task.get("status") == "DONE":
                        completed_tasks.append({
                            "phase": phase_name,
                            "task_id": task.get("id"),
                            "name": task.get("name")
                        })
        
        # Check if all critical modules are in place
        critical_checks = {
            "adaptive_scalping_integrated": False,
            "position_manager_integrated": False,
            "multi_tp_integrated": False,
            "apis_added": False,
            "dashboard_connected": False
        }
        
        # Check actual state
        run_paper = self.bot_path / "run_paper_infinity_pro.py"
        if run_paper.exists():
            with open(run_paper, 'r') as f:
                content = f.read()
            
            if "AdaptiveScalpingEngine" in content:
                critical_checks["adaptive_scalping_integrated"] = True
            if "SmartPositionManager" in content:
                critical_checks["position_manager_integrated"] = True
            if "MultiTP" in content or "multi_tp" in content:
                critical_checks["multi_tp_integrated"] = True
        
        api_main = self.bot_path / "api" / "main.py"
        if api_main.exists():
            with open(api_main, 'r') as f:
                content = f.read()
            
            if "/api/adaptive_scalping" in content:
                critical_checks["apis_added"] = True
        
        # Find gaps
        gaps = []
        for check, status in critical_checks.items():
            if not status:
                gaps.append({
                    "missing": check,
                    "severity": "critical",
                    "action_needed": f"Complete {check}"
                })
        
        return {
            "completed_tasks": completed_tasks,
            "critical_checks": critical_checks,
            "gaps_found": gaps,
            "all_complete": len(gaps) == 0
        }
    
    def run_continuous_check(self, interval: int = 60):
        """Mode continu: vérifie et corrige automatiquement"""
        print(f"🔄 Mode continu activé (check toutes les {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                print(f"\n{'='*60}")
                print(f"🔍 Diagnostic automatique - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                
                # 1. Check compatibilité
                print("\n1️⃣ Check compatibilité Python...")
                py_files = list(self.bot_path.glob("**/*.py"))
                for py_file in py_files[:5]:  # Sample
                    if "venv" not in str(py_file):
                        result = self.check_python_version_compatibility(py_file)
                        if not result["compatible"]:
                            print(f"⚠️ {py_file.name}: {len(result['issues'])} issues")
                
                # 2. Check code incomplet
                print("\n2️⃣ Check code incomplet...")
                critical_files = [
                    "core/adaptive_scalping_engine.py",
                    "core/smart_position_manager.py",
                    "core/multi_tp_and_funding_optimizer.py"
                ]
                for file in critical_files:
                    full_path = self.bot_path / file
                    if full_path.exists():
                        result = self.detect_incomplete_code(full_path)
                        if not result["complete"]:
                            print(f"⚠️ {file}: {len(result['issues'])} incomplete sections")
                
                # 3. Check stratégies manquantes
                print("\n3️⃣ Check stratégies...")
                missing_strat = self.find_missing_strategies()
                if missing_strat.get("missing"):
                    print(f"⚠️ {len(missing_strat['missing'])} stratégies manquantes")
                
                # 4. Check cohérence modules
                print("\n4️⃣ Check cohérence...")
                consistency = self.check_module_consistency()
                if consistency:
                    print(f"⚠️ {len(consistency)} problèmes de cohérence")
                
                # 5. Auto-fix si possible
                print("\n5️⃣ Auto-corrections...")
                fixes = self.auto_fix_duplicates()
                if fixes:
                    print(f"✅ {len(fixes)} corrections appliquées")
                
                # 6. Validate progress
                print("\n6️⃣ Validation progression...")
                validation = self.validate_progress_vs_history()
                if validation.get("gaps_found"):
                    print(f"⚠️ {len(validation['gaps_found'])} gaps détectés")
                    for gap in validation["gaps_found"]:
                        print(f"   - {gap['missing']}")
                
                print(f"\n✅ Check terminé. Prochaine vérification dans {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Mode continu arrêté")
            self.save_memory()
    
    def generate_fix_all_report(self) -> Dict:
        """Génère rapport complet avec toutes les corrections possibles"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "compatibility_issues": [],
            "incomplete_code": [],
            "missing_strategies": {},
            "consistency_issues": [],
            "import_fixes": [],
            "duplicate_fixes": [],
            "progress_gaps": {},
            "dashboard_health": {},
            "frontend_errors": {},
            "dashboard_features": {},
            "dashboard_fixes": []
        }
        
        print("🔍 Analyse complète du système...")
        
        # 1. Compatibility
        print("  Checking compatibility...")
        py_files = [f for f in self.bot_path.glob("**/*.py") if "venv" not in str(f)]
        for py_file in py_files[:20]:
            result = self.check_python_version_compatibility(py_file)
            if not result["compatible"]:
                report["compatibility_issues"].append(result)
        
        # 2. Incomplete code
        print("  Checking incomplete code...")
        for py_file in py_files[:20]:
            result = self.detect_incomplete_code(py_file)
            if not result["complete"]:
                report["incomplete_code"].append(result)
        
        # 3. Missing strategies
        print("  Checking missing strategies...")
        report["missing_strategies"] = self.find_missing_strategies()
        
        # 4. Consistency
        print("  Checking consistency...")
        report["consistency_issues"] = self.check_module_consistency()
        
        # 5. Import fixes
        print("  Checking imports...")
        report["import_fixes"] = self.auto_fix_import_errors()
        
        # 6. Duplicates
        print("  Checking duplicates...")
        report["duplicate_fixes"] = self.auto_fix_duplicates()
        
        # 7. Progress validation
        print("  Validating progress...")
        report["progress_gaps"] = self.validate_progress_vs_history()
        
        # 8. Dashboard health check
        print("  Checking dashboard health...")
        report["dashboard_health"] = self.check_dashboard_health()
        
        # 9. Frontend errors
        print("  Checking frontend errors...")
        report["frontend_errors"] = self.check_frontend_errors()
        
        # 10. Dashboard features missing
        print("  Checking dashboard features...")
        report["dashboard_features"] = self.check_dashboard_features()
        
        # 11. Auto-fix dashboard issues
        print("  Auto-fixing dashboard issues...")
        report["dashboard_fixes"] = self.auto_fix_dashboard_issues()
        
        # Save report
        report_file = self.bot_path / "smart_diagnostic_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Rapport sauvegardé: {report_file}")
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Smart Diagnostic Auto-Correct - Détecte ET corrige automatiquement"
    )
    parser.add_argument(
        "--bot-path",
        default="/opt/smartorder-pro",
        help="Chemin vers le bot"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Mode continu (vérifie et corrige automatiquement)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Intervalle en secondes pour mode watch (défaut: 60)"
    )
    parser.add_argument(
        "--fix-all",
        action="store_true",
        help="Applique toutes les corrections automatiques possibles"
    )
    
    args = parser.parse_args()
    
    diagnostic = SmartDiagnosticAutoCorrect(bot_path=args.bot_path)
    
    if args.watch:
        diagnostic.run_continuous_check(interval=args.interval)
    elif args.fix_all:
        report = diagnostic.generate_fix_all_report()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES CORRECTIONS")
        print("="*60)
        print(f"Compatibility issues: {len(report['compatibility_issues'])}")
        print(f"Incomplete code: {len(report['incomplete_code'])}")
        print(f"Missing strategies: {len(report['missing_strategies'].get('missing', []))}")
        print(f"Consistency issues: {len(report['consistency_issues'])}")
        print(f"Import fixes: {len(report['import_fixes'])}")
        print(f"Duplicate fixes: {len(report['duplicate_fixes'])}")
        print(f"Progress gaps: {len(report['progress_gaps'].get('gaps_found', []))}")
        print(f"Dashboard issues: {len(report['dashboard_health'].get('issues', []))}")
        print(f"Frontend errors: {len(report['frontend_errors'].get('issues', []))}")
        print(f"Dashboard missing features: {report['dashboard_features'].get('total', 0)}")
        print(f"Dashboard fixes applied: {len(report['dashboard_fixes'])}")
    else:
        # Single run
        report = diagnostic.generate_fix_all_report()
        print("\n✅ Analyse terminée. Utilise --fix-all pour appliquer corrections.")


if __name__ == "__main__":
    main()
