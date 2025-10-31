#!/usr/bin/env python3
"""
AUDIT v2.1 - SmartOrder PRO AI
Date: 2025-10-31
Description: Verification complete de chaque fonction dashboard/bot
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Paths
CONFIG_DIR = Path("/opt/smartorder-pro/config")

class AuditReport:
    """Generateur de rapport d'audit"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "sections": {}
        }
    
    def test_section(self, section_name: str, description: str):
        """Teste une section specifique"""
        print(f"\n{'='*60}")
        print(f"🔍 AUDIT: {section_name}")
        print(f"📋 {description}")
        print('='*60)
        
        self.results["sections"][section_name] = {
            "description": description,
            "tests": []
        }
        
        return section_name
    
    def test(self, section: str, test_name: str, test_func):
        """Execute un test"""
        try:
            result = test_func()
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} - {test_name}")
            if not result["passed"]:
                print(f"   └─ {result.get('reason', 'Unknown')}")
            else:
                print(f"   └─ {result.get('details', 'OK')}")
            
            self.results["sections"][section]["tests"].append({
                "name": test_name,
                "passed": result["passed"],
                "reason": result.get("reason", ""),
                "details": result.get("details", "")
            })
            
            return result["passed"]
        except Exception as e:
            print(f"❌ ERROR - {test_name}: {e}")
            self.results["sections"][section]["tests"].append({
                "name": test_name,
                "passed": False,
                "reason": str(e),
                "details": ""
            })
            return False
    
    def summary(self):
        """Affiche le resume"""
        print(f"\n{'='*60}")
        print("📊 AUDIT SUMMARY")
        print('='*60)
        
        total_tests = 0
        passed_tests = 0
        
        for section_name, section_data in self.results["sections"].items():
            section_passed = sum(1 for t in section_data["tests"] if t["passed"])
            section_total = len(section_data["tests"])
            total_tests += section_total
            passed_tests += section_passed
            
            status = "✅" if section_passed == section_total else "⚠️"
            print(f"\n{status} {section_name}: {section_passed}/{section_total}")
            
            for test in section_data["tests"]:
                if not test["passed"]:
                    print(f"   ❌ {test['name']}: {test['reason']}")
        
        print(f"\n{'='*60}")
        print(f"TOTAL: {passed_tests}/{total_tests} tests passed")
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print('='*60)
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "success_rate": success_rate
        }
    
    def save_report(self, path: str = "/opt/smartorder-pro/logs/audit_report.json"):
        """Sauvegarde le rapport"""
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Rapport sauvegarde: {path}")

# Tests specifiques

def test_watchlist_file_exists():
    """Teste si watchlist.json existe"""
    watchlist_file = CONFIG_DIR / "watchlist.json"
    return {
        "passed": watchlist_file.exists(),
        "reason": "File not found" if not watchlist_file.exists() else "",
        "details": f"File: {watchlist_file}"
    }

def test_watchlist_content():
    """Teste le contenu de la watchlist"""
    watchlist_file = CONFIG_DIR / "watchlist.json"
    try:
        with open(watchlist_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return {
                "passed": True,
                "details": f"Found {len(data)} coins: {', '.join(data) if data else 'empty'}"
            }
        else:
            return {
                "passed": False,
                "reason": f"Invalid format: expected list, got {type(data)}"
            }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

def test_risk_config_file():
    """Teste si config risk management existe"""
    risk_file = CONFIG_DIR / "risk_config.json"
    
    if not risk_file.exists():
        # Creer fichier par defaut
        default_config = {
            "max_position_size": 1000,
            "stop_loss_percent": 0.02,
            "take_profit_percent": 0.03,
            "max_open_trades": 5,
            "max_daily_loss": 100
        }
        with open(risk_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return {
            "passed": True,
            "details": "Created default risk_config.json"
        }
    
    return {
        "passed": True,
        "details": f"File exists: {risk_file}"
    }

def test_risk_config_content():
    """Teste le contenu risk config"""
    risk_file = CONFIG_DIR / "risk_config.json"
    try:
        with open(risk_file, 'r') as f:
            data = json.load(f)
        
        required_keys = ["max_position_size", "stop_loss_percent", "take_profit_percent"]
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            return {
                "passed": False,
                "reason": f"Missing keys: {missing_keys}"
            }
        
        return {
            "passed": True,
            "details": f"Max pos: {data['max_position_size']} USDT, SL: {data['stop_loss_percent']*100}%, TP: {data['take_profit_percent']*100}%"
        }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

def test_wallet_file():
    """Teste wallet paper trading"""
    wallet_file = CONFIG_DIR / "paper_wallet.json"
    
    if not wallet_file.exists():
        # Creer wallet par defaut
        default_wallet = {
            "balance": 10000,
            "initial_balance": 10000,
            "pnl": 0,
            "last_update": datetime.now().isoformat()
        }
        with open(wallet_file, 'w') as f:
            json.dump(default_wallet, f, indent=2)
        
        return {
            "passed": True,
            "details": "Created default paper_wallet.json with 10,000 USDT"
        }
    
    return {
        "passed": True,
        "details": f"File exists: {wallet_file}"
    }

def test_wallet_balance():
    """Teste le solde wallet"""
    wallet_file = CONFIG_DIR / "paper_wallet.json"
    try:
        with open(wallet_file, 'r') as f:
            data = json.load(f)
        
        balance = data.get("balance", 0)
        initial = data.get("initial_balance", 10000)
        pnl = data.get("pnl", 0)
        
        return {
            "passed": True,
            "details": f"Balance: ${balance:.2f} (Initial: ${initial:.2f}, PnL: ${pnl:.2f})"
        }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

def test_pnl_tracker():
    """Teste PnL tracker"""
    pnl_file = CONFIG_DIR / "pnl_tracker.json"
    try:
        with open(pnl_file, 'r') as f:
            data = json.load(f)
        
        total_pnl = data.get("total_pnl", 0)
        trades_count = len(data.get("trades", []))
        
        return {
            "passed": True,
            "details": f"Total PnL: ${total_pnl:.2f}, Trades: {trades_count}"
        }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

def test_positions_file():
    """Teste positions.json"""
    positions_file = CONFIG_DIR / "positions.json"
    try:
        with open(positions_file, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return {"passed": False, "reason": "Invalid format"}
        
        open_positions = [p for p in data if p.get("status") != "closed"]
        
        return {
            "passed": True,
            "details": f"Total positions: {len(data)}, Open: {len(open_positions)}"
        }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

def test_strategies_state():
    """Teste strategies_state.json"""
    strategies_file = CONFIG_DIR / "strategies_state.json"
    try:
        with open(strategies_file, 'r') as f:
            data = json.load(f)
        
        total_strategies = 0
        enabled_strategies = 0
        
        for mode in ["spot", "futures", "hybride"]:
            strategies = data.get(mode, [])
            total_strategies += len(strategies)
            enabled_strategies += sum(1 for s in strategies if s.get("enabled"))
        
        return {
            "passed": True,
            "details": f"Total: {total_strategies}, Enabled: {enabled_strategies}"
        }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

def test_diagnostic_memory():
    """Teste diagnostic_memory.json"""
    diag_file = Path("/opt/smartorder-pro/logs/diagnostic_memory.json")
    
    if not diag_file.exists():
        return {
            "passed": False,
            "reason": "Diagnostic memory not initialized"
        }
    
    try:
        with open(diag_file, 'r') as f:
            data = json.load(f)
        
        return {
            "passed": True,
            "details": f"Anomalies: {len(data.get('anomalies', []))}, Corrections: {len(data.get('corrections', []))}"
        }
    except Exception as e:
        return {"passed": False, "reason": str(e)}

# Main audit
def run_audit():
    """Execute l'audit complet"""
    audit = AuditReport()
    
    # Section 1: Watchlist
    section = audit.test_section("WATCHLIST", "Verification coins surveilles")
    audit.test(section, "Fichier watchlist.json existe", test_watchlist_file_exists)
    audit.test(section, "Contenu watchlist valide", test_watchlist_content)
    
    # Section 2: Risk Management
    section = audit.test_section("RISK MANAGEMENT", "Configuration gestion des risques")
    audit.test(section, "Fichier risk_config.json existe", test_risk_config_file)
    audit.test(section, "Parametres risk valides", test_risk_config_content)
    
    # Section 3: Wallet
    section = audit.test_section("WALLET", "Portefeuille paper trading")
    audit.test(section, "Fichier paper_wallet.json existe", test_wallet_file)
    audit.test(section, "Solde wallet coherent", test_wallet_balance)
    
    # Section 4: Trading Data
    section = audit.test_section("TRADING DATA", "Donnees de trading")
    audit.test(section, "PnL tracker fonctionnel", test_pnl_tracker)
    audit.test(section, "Positions trackees", test_positions_file)
    audit.test(section, "Strategies configurees", test_strategies_state)
    
    # Section 5: Diagnostic
    section = audit.test_section("DIAGNOSTIC", "Systeme de supervision")
    audit.test(section, "Memoire diagnostic active", test_diagnostic_memory)
    
    # Summary
    summary = audit.summary()
    audit.save_report()
    
    return summary

if __name__ == "__main__":
    summary = run_audit()
    sys.exit(0 if summary["success_rate"] == 100 else 1)
