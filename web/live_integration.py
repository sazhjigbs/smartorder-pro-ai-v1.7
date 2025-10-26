#!/usr/bin/env python3
"""
🌐 SAFELOGIC SmartOrder PRO — Live Integration Module
Intégration des modules Phase 6.11-6.14 au Portal Web
"""

import sys
import os
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.pnl_live import start as pnl_start, get as pnl_get
    from core.trust_memory_ai import start as trust_start, get as trust_get
    from core.smart_execution import start as exec_start, get as exec_get
    from core.market_context_ai import start as ctx_start, get as ctx_get
    
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module import error: {e}")
    MODULES_AVAILABLE = False

class LiveIntegration:
    def __init__(self):
        self.started = False
        
    def start_all_modules(self):
        """Start all Phase 6.11-6.14 modules"""
        if not MODULES_AVAILABLE:
            return {"error": "Modules not available"}
            
        try:
            if not self.started:
                print("🚀 Starting all live modules...")
                
                # Start PNL Live (Phase 6.11)
                pnl_start()
                print("✅ PNL Live started")
                
                # Start Trust Memory AI (Phase 6.12)  
                trust_start()
                print("✅ Trust Memory AI started")
                
                # Start Smart Execution (Phase 6.13)
                exec_start()
                print("✅ Smart Execution started")
                
                # Start Market Context AI (Phase 6.14)
                ctx_start()
                print("✅ Market Context AI started")
                
                self.started = True
                print("🎯 All modules started successfully!")
                
            return {"status": "started", "modules": 4}
            
        except Exception as e:
            print(f"❌ Error starting modules: {str(e)}")
            return {"error": str(e)}
    
    def get_live_status(self):
        """Get combined live status from all modules"""
        if not MODULES_AVAILABLE:
            return {"error": "Modules not available"}
            
        try:
            import time
            
            # Ensure modules are started
            self.start_all_modules()
            
            # Collect data from all modules
            status = {
                "pnl": pnl_get(),
                "trust": trust_get(), 
                "executions": exec_get(),
                "context": ctx_get(),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "live"
            }
            
            return status
            
        except Exception as e:
            return {"error": str(e), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

# Global instance
live_integration = LiveIntegration()

def start_live_modules():
    """Start all live modules"""
    return live_integration.start_all_modules()

def get_live_status():
    """Get live status from all modules"""
    return live_integration.get_live_status()

if __name__ == "__main__":
    # Test mode
    print("🧪 Testing Live Integration...")
    
    result = start_live_modules()
    print(f"Start result: {result}")
    
    import time
    time.sleep(2)
    
    status = get_live_status()
    print(f"Live status: {status}")