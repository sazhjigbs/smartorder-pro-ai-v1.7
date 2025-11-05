#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC INTELLIGENT - SmartOrder PRO AI v1.7
Détecte fichiers dupliqués, incohérences, et génère rapport détaillé

by MAIGA ABOUBAKR - SAFELOGIC
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import subprocess

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

class DiagnosticIntelligent:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "duplicates": [],
            "api_endpoints": {},
            "dashboards": [],
            "core_modules": [],
            "issues": [],
            "recommendations": []
        }
        
    def scan_dashboards(self):
        """Scan tous les fichiers dashboard dans web/"""
        print("\n🔍 [1/6] Scanning dashboards...")
        
        web_dir = self.base_path / "web"
        if not web_dir.exists():
            self.report["issues"].append("⚠️ Dossier /web introuvable")
            return
        
        # Chercher tous les fichiers HTML contenant "dashboard"
        dashboard_files = []
        for ext in ['*.html', '*.htm']:
            dashboard_files.extend(web_dir.rglob(ext))
        
        dashboard_files = [f for f in dashboard_files if 'dashboard' in f.name.lower()]
        
        for file in dashboard_files:
            stat = file.stat()
            dashboard_files.append({
                "name": file.name,
                "path": str(file.relative_to(self.base_path)),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "md5": self.get_md5(file)
            })
        
        self.report["dashboards"] = dashboard_files
        
        if len(dashboard_files) > 1:
            self.report["issues"].append(
                f"⚠️ {len(dashboard_files)} dashboards trouvés - fragmentation détectée"
            )
            self.report["recommendations"].append(
                "📌 Consolider vers un seul dashboard unifié: web/dashboard_unified_v2.4.html"
            )
        
        print(f"   ✅ {len(dashboard_files)} dashboards trouvés")
        
    def scan_api_routes(self):
        """Scan tous les fichiers API routes"""
        print("\n🔍 [2/6] Scanning API routes...")
        
        api_dir = self.base_path / "api"
        if not api_dir.exists():
            self.report["issues"].append("⚠️ Dossier /api introuvable")
            return
        
        # Chercher tous les fichiers Python contenant "route" ou "api"
        api_files = []
        for pattern in ['*route*.py', '*api*.py', 'app.py', 'main.py']:
            api_files.extend(api_dir.rglob(pattern))
        
        endpoints_found = defaultdict(list)
        
        for file in api_files:
            # Analyser les endpoints définis
            try:
                content = file.read_text(encoding='utf-8')
                # Chercher @app.route, @router.get, etc.
                import re
                routes = re.findall(r'@\w+\.(get|post|put|delete|route)\(["\']([^"\']+)', content)
                
                for method, route in routes:
                    endpoints_found[route].append({
                        "file": str(file.relative_to(self.base_path)),
                        "method": method
                    })
            except Exception as e:
                self.report["issues"].append(f"⚠️ Erreur lecture {file.name}: {e}")
        
        self.report["api_endpoints"] = dict(endpoints_found)
        
        # Détecter doublons d'endpoints
        duplicates = {k: v for k, v in endpoints_found.items() if len(v) > 1}
        if duplicates:
            self.report["issues"].append(
                f"⚠️ {len(duplicates)} endpoints dupliqués détectés"
            )
            for endpoint, files in duplicates.items():
                self.report["issues"].append(
                    f"   • {endpoint} défini dans: {', '.join([f['file'] for f in files])}"
                )
        
        print(f"   ✅ {len(endpoints_found)} endpoints trouvés")
        
    def scan_core_modules(self):
        """Scan modules core pour détecter doublons"""
        print("\n🔍 [3/6] Scanning core modules...")
        
        core_dir = self.base_path / "core"
        if not core_dir.exists():
            self.report["issues"].append("⚠️ Dossier /core introuvable")
            return
        
        # Chercher fichiers importants
        key_modules = [
            "autoexec_engine.py",
            "execution_engine.py",
            "auto_trading_engine.py",
            "multi_exchange_manager.py",
            "bybit_client.py",
            "router.py"
        ]
        
        found_modules = []
        for module in key_modules:
            matches = list(core_dir.rglob(module))
            if matches:
                for match in matches:
                    found_modules.append({
                        "name": module,
                        "path": str(match.relative_to(self.base_path)),
                        "exists": True,
                        "md5": self.get_md5(match)
                    })
            else:
                found_modules.append({
                    "name": module,
                    "path": None,
                    "exists": False
                })
        
        self.report["core_modules"] = found_modules
        
        # Modules manquants
        missing = [m for m in found_modules if not m["exists"]]
        if missing:
            self.report["recommendations"].append(
                f"📌 Créer modules manquants: {', '.join([m['name'] for m in missing])}"
            )
        
        print(f"   ✅ {len([m for m in found_modules if m['exists']])} modules core trouvés")
        
    def check_duplicates_by_hash(self):
        """Détecter fichiers dupliqués par hash MD5"""
        print("\n🔍 [4/6] Checking duplicate files by hash...")
        
        hashes = defaultdict(list)
        
        # Scanner tous les fichiers Python et HTML
        for ext in ['**/*.py', '**/*.html']:
            for file in self.base_path.glob(ext):
                if 'venv' in str(file) or '__pycache__' in str(file):
                    continue
                
                file_hash = self.get_md5(file)
                hashes[file_hash].append(str(file.relative_to(self.base_path)))
        
        # Trouver doublons
        duplicates = {k: v for k, v in hashes.items() if len(v) > 1}
        
        if duplicates:
            self.report["duplicates"] = [
                {"hash": h, "files": files} 
                for h, files in duplicates.items()
            ]
            self.report["issues"].append(
                f"⚠️ {len(duplicates)} groupes de fichiers identiques détectés"
            )
        
        print(f"   ✅ {len(duplicates)} doublons détectés")
        
    def check_ports(self):
        """Vérifier ports ouverts (Windows compatible)"""
        print("\n🔍 [5/6] Checking open ports...")
        
        expected_ports = {
            "8555": "Portal Web Principal",
            "8614": "API Phase 6.14",
            "8765": "WebSocket",
            "5000": "Config Manager",
            "8181": "Dashboard Unifié (attendu)"
        }
        
        try:
            # Windows: netstat -ano
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            ports_open = {}
            for port, desc in expected_ports.items():
                if f":{port}" in result.stdout:
                    ports_open[port] = {"status": "OPEN", "description": desc}
                else:
                    ports_open[port] = {"status": "CLOSED", "description": desc}
            
            self.report["ports"] = ports_open
            
            closed = [p for p, info in ports_open.items() if info["status"] == "CLOSED"]
            if closed:
                self.report["recommendations"].append(
                    f"📌 Ports fermés: {', '.join(closed)} - vérifier services"
                )
            
            print(f"   ✅ {len([p for p in ports_open.values() if p['status'] == 'OPEN'])} ports ouverts")
            
        except Exception as e:
            self.report["issues"].append(f"⚠️ Impossible vérifier ports: {e}")
            print(f"   ⚠️ Erreur vérification ports")
    
    def check_systemd_services(self):
        """Vérifier services systemd (Linux uniquement)"""
        print("\n🔍 [6/8] Checking systemd services...")
        
        required_services = [
            "smartorder-websync-bridge.service",
            "smartorder-fusion-ai.service",
            "smartorder-portal-v5.service",
            "smartorder-guardian.service"
        ]
        
        services_status = {}
        
        try:
            # Vérifier si systemctl est disponible
            result = subprocess.run(
                ["systemctl", "--version"],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0:
                for service in required_services:
                    try:
                        check = subprocess.run(
                            ["systemctl", "is-active", service],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        is_active = check.stdout.strip() == "active"
                        services_status[service] = "active" if is_active else "inactive"
                    except Exception:
                        services_status[service] = "unknown"
                
                self.report["systemd_services"] = services_status
                
                missing = [s for s, status in services_status.items() if status != "active"]
                if missing:
                    self.report["issues"].append(
                        f"⚠️ Services inactifs: {', '.join(missing)}"
                    )
                
                print(f"   ✅ {len([s for s in services_status.values() if s == 'active'])} services actifs")
            else:
                print("   ⚠️ Systemd non disponible (Windows)")
                self.report["systemd_services"] = {"available": False}
                
        except FileNotFoundError:
            print("   ⚠️ Systemd non disponible (Windows)")
            self.report["systemd_services"] = {"available": False}
        except Exception as e:
            self.report["issues"].append(f"⚠️ Erreur vérification systemd: {e}")
            print(f"   ⚠️ Erreur systemd")
    
    def check_environment(self):
        """Vérifier environnement Python et dépendances"""
        print("\n🔍 [7/8] Checking environment...")
        
        import platform
        
        env_info = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "architecture": platform.machine()
        }
        
        # Vérifier ccxt
        try:
            import ccxt
            env_info["ccxt_version"] = ccxt.__version__
            
            # Vérifier version ccxt >= 4.2.4
            ccxt_major, ccxt_minor, ccxt_patch = ccxt.__version__.split('.')[:3]
            if int(ccxt_major) < 4 or (int(ccxt_major) == 4 and int(ccxt_minor) < 2):
                self.report["issues"].append(
                    f"⚠️ ccxt version {ccxt.__version__} < 4.2.4 requise"
                )
        except ImportError:
            env_info["ccxt_version"] = "not installed"
            self.report["issues"].append("⚠️ ccxt non installé (requis)")
        
        # Vérifier autres dépendances critiques
        critical_deps = ['flask', 'aiohttp', 'websocket', 'psutil', 'pandas']
        missing_deps = []
        
        for dep in critical_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            env_info["missing_dependencies"] = missing_deps
            self.report["issues"].append(
                f"⚠️ Dépendances manquantes: {', '.join(missing_deps)}"
            )
        
        self.report["environment"] = env_info
        print(f"   ✅ Python {env_info['python_version']}, ccxt {env_info.get('ccxt_version', 'N/A')}")
    
    def check_config_files(self):
        """Vérifier fichiers de configuration"""
        print("\n🔍 [8/8] Checking configuration files...")
        
        config_files = [
            "config/exchanges.json",
            "config/bot_config.json",
            "config/trading_coins.json",
            "config/state.json",
            ".env"
        ]
        
        config_status = {}
        for config in config_files:
            path = self.base_path / config
            if path.exists():
                config_status[config] = {
                    "exists": True,
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                }
            else:
                config_status[config] = {"exists": False}
                self.report["issues"].append(f"⚠️ Config manquant: {config}")
        
        self.report["config_files"] = config_status
        print(f"   ✅ {len([c for c in config_status.values() if c['exists']])} configs trouvés")
    
    def get_md5(self, filepath):
        """Calculer hash MD5 d'un fichier"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def generate_report(self):
        """Générer rapport final"""
        print("\n" + "="*60)
        print("📊 RAPPORT DE DIAGNOSTIC")
        print("="*60)
        
        # Résumé
        total_issues = len(self.report["issues"])
        total_recommendations = len(self.report["recommendations"])
        
        print(f"\n📌 Résumé:")
        print(f"   • Dashboards trouvés: {len(self.report['dashboards'])}")
        print(f"   • Endpoints API: {len(self.report['api_endpoints'])}")
        print(f"   • Modules core: {len([m for m in self.report['core_modules'] if m['exists']])}")
        print(f"   • Fichiers dupliqués: {len(self.report['duplicates'])}")
        print(f"   • Issues: {total_issues}")
        print(f"   • Recommandations: {total_recommendations}")
        
        # Issues
        if self.report["issues"]:
            print(f"\n⚠️ Issues détectés:")
            for issue in self.report["issues"]:
                print(f"   {issue}")
        
        # Recommandations
        if self.report["recommendations"]:
            print(f"\n💡 Recommandations:")
            for rec in self.report["recommendations"]:
                print(f"   {rec}")
        
        # Sauvegarder rapport JSON
        report_path = self.base_path / "logs" / "diagnostic_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Rapport sauvegardé: {report_path}")
        
        # Sauvegarder rapport texte
        report_txt = self.base_path / "logs" / "diagnostic_report.log"
        with open(report_txt, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("🔍 DIAGNOSTIC INTELLIGENT - SmartOrder PRO AI v1.7\n")
            f.write(f"Date: {self.report['timestamp']}\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"📌 RÉSUMÉ\n")
            f.write(f"Dashboards: {len(self.report['dashboards'])}\n")
            f.write(f"Endpoints API: {len(self.report['api_endpoints'])}\n")
            f.write(f"Issues: {total_issues}\n")
            f.write(f"Recommandations: {total_recommendations}\n\n")
            
            if self.report["issues"]:
                f.write("⚠️ ISSUES\n")
                for issue in self.report["issues"]:
                    f.write(f"{issue}\n")
                f.write("\n")
            
            if self.report["recommendations"]:
                f.write("💡 RECOMMANDATIONS\n")
                for rec in self.report["recommendations"]:
                    f.write(f"{rec}\n")
                f.write("\n")
        
        print(f"✅ Rapport texte: {report_txt}")
        print("\n" + "="*60)

def main():
    """Point d'entrée principal"""
    print("🔍 DIAGNOSTIC INTELLIGENT - SmartOrder PRO AI v1.7")
    print("by MAIGA ABOUBAKR - SAFELOGIC\n")
    
    # Déterminer base path
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = Path(__file__).parent.parent
    
    print(f"📁 Base path: {base_path}\n")
    
    # Créer diagnostic
    diag = DiagnosticIntelligent(base_path)
    
    # Exécuter scans
    diag.scan_dashboards()
    diag.scan_api_routes()
    diag.scan_core_modules()
    diag.check_duplicates_by_hash()
    diag.check_ports()
    diag.check_systemd_services()
    diag.check_environment()
    diag.check_config_files()
    
    # Générer rapport
    diag.generate_report()
    
    print("\n✅ Diagnostic terminé!")

if __name__ == "__main__":
    main()
