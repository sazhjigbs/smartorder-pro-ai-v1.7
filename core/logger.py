#!/usr/bin/env python3
"""
📝 SAFELOGIC SmartOrder PRO — Structured Logger
Ultra-léger, optimisé pour VPS faible RAM
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Config paths VPS
LOG_DIR = Path("/opt/smartorder-pro/logs")
MAX_LOG_SIZE_MB = 10  # Rotation à 10MB (économie disque)
MAX_LOG_FILES = 3  # Garde 3 fichiers max

class StreamLogger:
    """Logger ultra-léger avec rotation automatique"""
    
    def __init__(self, name="smartorder"):
        self.name = name
        self.log_dir = LOG_DIR
        
        # Crée dossier logs
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Fichier du jour
        self.log_file = self.get_log_file()
    
    def get_log_file(self):
        """Fichier log du jour"""
        today = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"{self.name}_{today}.jsonl"
    
    def rotate_if_needed(self):
        """Rotation si fichier trop gros"""
        try:
            if self.log_file.exists():
                size_mb = self.log_file.stat().st_size / (1024 * 1024)
                
                if size_mb > MAX_LOG_SIZE_MB:
                    # Archive ancien fichier
                    timestamp = datetime.now().strftime("%H%M%S")
                    archive_name = f"{self.log_file.stem}_{timestamp}.jsonl"
                    self.log_file.rename(self.log_dir / archive_name)
                    
                    # Nettoie vieux logs
                    self.cleanup_old_logs()
        except:
            pass
    
    def cleanup_old_logs(self):
        """Garde seulement N derniers logs"""
        try:
            logs = sorted(self.log_dir.glob(f"{self.name}_*.jsonl"))
            
            if len(logs) > MAX_LOG_FILES:
                for old_log in logs[:-MAX_LOG_FILES]:
                    old_log.unlink()
        except:
            pass
    
    def _write(self, level, message, **kwargs):
        """Écrit log (une seule ligne JSON)"""
        try:
            # Rotation check
            self.rotate_if_needed()
            
            # Log entry
            entry = {
                "ts": datetime.now().isoformat(),
                "lvl": level,
                "msg": message,
                **kwargs
            }
            
            # Écrit en append (économie RAM)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            # Console aussi
            print(f"[{entry['ts']}] {level} - {message}")
            
        except Exception as e:
            # Fallback console si échec
            print(f"LOG ERROR: {str(e)}")
    
    def info(self, message, **kwargs):
        """Log INFO"""
        self._write("INFO", message, **kwargs)
    
    def error(self, message, **kwargs):
        """Log ERROR"""
        self._write("ERROR", message, **kwargs)
    
    def warning(self, message, **kwargs):
        """Log WARNING"""
        self._write("WARN", message, **kwargs)
    
    def trade(self, action, symbol, price, quantity, **kwargs):
        """Log TRADE spécial"""
        self._write("TRADE",
            f"{action} {quantity} {symbol} @ {price}",
            action=action,
            symbol=symbol,
            price=price,
            qty=quantity,
            **kwargs
        )
    
    def health(self, cpu, ram, status="ok", **kwargs):
        """Log HEALTH check"""
        self._write("HEALTH",
            f"CPU:{cpu}% RAM:{ram}% [{status}]",
            cpu=cpu,
            ram=ram,
            status=status,
            **kwargs
        )

# Singleton global
logger = StreamLogger()

# Raccourcis
def info(msg, **kw): logger.info(msg, **kw)
def error(msg, **kw): logger.error(msg, **kw)
def warning(msg, **kw): logger.warning(msg, **kw)
def trade(action, symbol, price, qty, **kw): logger.trade(action, symbol, price, qty, **kw)
def health(cpu, ram, status="ok", **kw): logger.health(cpu, ram, status, **kw)

# Test
if __name__ == "__main__":
    info("Logger test started")
    trade("BUY", "BTCUSDT", 67000, 0.001, exchange="bybit")
    health(12.5, 22.0, status="healthy")
    error("Test error", code=500)
    print("✅ Logger test complete")
