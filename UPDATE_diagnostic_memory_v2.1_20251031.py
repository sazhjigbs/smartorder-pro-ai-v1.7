#!/usr/bin/env python3
"""
UPDATE: Diagnostic Memory Module v2.1
Date: 2025-10-31
Description: Systeme de memoire diagnostic anti-regression
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DiagnosticMemory:
    """Memoire diagnostic pour tracker anomalies et corrections"""
    
    def __init__(self, memory_path: str = "/opt/smartorder-pro/logs/diagnostic_memory.json"):
        self.memory_path = Path(memory_path)
        self.memory = self._load_memory()
        
    def _load_memory(self) -> Dict:
        """Charge la memoire depuis le fichier"""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur chargement memoire: {e}")
        
        return {
            "version": "v2.1",
            "created_at": datetime.now().isoformat(),
            "last_check": None,
            "anomalies": [],
            "corrections": [],
            "validated_modules": [],
            "snapshots": []
        }
    
    def _save_memory(self):
        """Sauvegarde la memoire"""
        try:
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_path, 'w') as f:
                json.dump(self.memory, f, indent=2)
            logger.debug(f"Memoire sauvegardee: {self.memory_path}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde memoire: {e}")
    
    def record_anomaly(self, module: str, description: str, severity: str = "warning"):
        """Enregistre une anomalie detectee"""
        anomaly = {
            "id": len(self.memory["anomalies"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "description": description,
            "severity": severity,
            "status": "open"
        }
        
        self.memory["anomalies"].append(anomaly)
        self._save_memory()
        logger.warning(f"Anomalie enregistree: {module} - {description}")
        
        return anomaly["id"]
    
    def record_correction(self, anomaly_id: Optional[int], module: str, action: str, success: bool = True):
        """Enregistre une correction appliquee"""
        correction = {
            "id": len(self.memory["corrections"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "anomaly_id": anomaly_id,
            "module": module,
            "action": action,
            "success": success
        }
        
        self.memory["corrections"].append(correction)
        
        # Marquer anomalie comme corrigee
        if anomaly_id:
            for anomaly in self.memory["anomalies"]:
                if anomaly.get("id") == anomaly_id:
                    anomaly["status"] = "resolved" if success else "failed"
                    break
        
        self._save_memory()
        logger.info(f"Correction enregistree: {module} - {action}")
        
        return correction["id"]
    
    def validate_module(self, module: str, version: str, tests_passed: bool = True):
        """Valide un module comme fonctionnel"""
        validation = {
            "module": module,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "tests_passed": tests_passed
        }
        
        # Remplacer validation existante
        self.memory["validated_modules"] = [
            v for v in self.memory["validated_modules"] 
            if v.get("module") != module
        ]
        
        self.memory["validated_modules"].append(validation)
        self._save_memory()
        logger.info(f"Module valide: {module} v{version}")
    
    def create_snapshot(self, description: str, files: List[str]):
        """Cree un snapshot de l'etat actuel"""
        snapshot = {
            "id": len(self.memory["snapshots"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "files": files,
            "validated_modules": len(self.memory["validated_modules"])
        }
        
        self.memory["snapshots"].append(snapshot)
        self._save_memory()
        logger.info(f"Snapshot cree: {description}")
        
        return snapshot["id"]
    
    def get_status(self) -> Dict:
        """Retourne le statut actuel"""
        open_anomalies = [a for a in self.memory["anomalies"] if a.get("status") == "open"]
        
        return {
            "version": self.memory.get("version"),
            "last_check": self.memory.get("last_check"),
            "total_anomalies": len(self.memory["anomalies"]),
            "open_anomalies": len(open_anomalies),
            "total_corrections": len(self.memory["corrections"]),
            "validated_modules": len(self.memory["validated_modules"]),
            "snapshots": len(self.memory["snapshots"])
        }
    
    def update_check(self):
        """Met a jour le timestamp de derniere verification"""
        self.memory["last_check"] = datetime.now().isoformat()
        self._save_memory()

# Test du module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== DIAGNOSTIC MEMORY TEST ===")
    
    diag = DiagnosticMemory()
    
    # Test anomalie
    anomaly_id = diag.record_anomaly("risk_manager", "Module manquant", "error")
    print(f"Anomalie enregistree: ID {anomaly_id}")
    
    # Test correction
    correction_id = diag.record_correction(anomaly_id, "risk_manager", "UPDATE_risk_management_v2.1 applique", True)
    print(f"Correction enregistree: ID {correction_id}")
    
    # Test validation
    diag.validate_module("risk_manager", "v2.1", True)
    diag.validate_module("technical_indicators", "v2.1", True)
    diag.validate_module("ccxt_integration", "v2.1", True)
    print("Modules valides")
    
    # Test snapshot
    snapshot_id = diag.create_snapshot("v2.1 Updates complets", [
        "UPDATE_risk_management_v2.1_20251031.py",
        "UPDATE_technical_indicators_v2.1_20251031.py",
        "UPDATE_ccxt_integration_v2.1_20251031.py"
    ])
    print(f"Snapshot cree: ID {snapshot_id}")
    
    # Status
    status = diag.get_status()
    print(f"\nStatus: {status}")
    print(f"Fichier memoire: {diag.memory_path}")
