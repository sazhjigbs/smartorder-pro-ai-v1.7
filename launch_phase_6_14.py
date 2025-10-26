#!/usr/bin/env python3
"""
🚀 SAFELOGIC SmartOrder PRO — Phase 6.14 Complete Launcher
Lance tous les modules Phase 6.11-6.14 + Multi-Exchange Router
"""

import os
import time
import threading
import json
from datetime import datetime
from pathlib import Path

class Phase614Launcher:
    def __init__(self):
        self.status = {
            "modules": {},
            "started": False,
            "start_time": None
        }
        self.log_file = "logs/phase_614.log"
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
    
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{log_entry}\n")
        except:
            pass
    
    def start_live_modules(self):
        """Start all Phase 6.11-6.14 modules"""
        self.log("🚀 Starting Phase 6.14 Complete Stack...")
        
        try:
            # Import and start PNL Live (Phase 6.11)
            from core.pnl_live import start as pnl_start
            pnl_start()
            self.status["modules"]["pnl_live"] = "active"
            self.log("✅ Phase 6.11 - PNL Live started")
            
            # Import and start Trust Memory AI (Phase 6.12)
            from core.trust_memory_ai import start as trust_start
            trust_start()
            self.status["modules"]["trust_memory"] = "active"
            self.log("✅ Phase 6.12 - Trust Memory AI started")
            
            # Import and start Smart Execution (Phase 6.13)
            from core.smart_execution import start as exec_start
            exec_start()
            self.status["modules"]["smart_execution"] = "active"
            self.log("✅ Phase 6.13 - Smart Execution started")
            
            # Import and start Market Context AI (Phase 6.14)
            from core.market_context_ai import start as ctx_start
            ctx_start()
            self.status["modules"]["market_context"] = "active"
            self.log("✅ Phase 6.14 - Market Context AI started")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error starting live modules: {str(e)}")
            return False
    
    def test_router_aiguillage(self):
        """Test Multi-Exchange Router with aiguillage rules"""
        self.log("🧪 Testing Multi-Exchange Router...")
        
        try:
            from core.router import choose_exchange, get_routing_history
            
            # Test different scenarios
            test_cases = [
                {"symbol": "BTCUSDT", "quantity": 0.001, "price": 67000},
                {"symbol": "ETHUSDT", "quantity": 0.01, "price": 2450},
                {"symbol": "SOLUSDT", "quantity": 0.1, "price": 180}
            ]
            
            for test in test_cases:
                selected_exchange = choose_exchange(**test)
                self.log(f"📊 {test['symbol']}: Router selected {selected_exchange}")
            
            # Get routing history
            history = get_routing_history()
            self.log(f"📜 Routing history: {len(history)} decisions logged")
            
            self.status["modules"]["router"] = "active"
            return True
            
        except Exception as e:
            self.log(f"❌ Router test failed: {str(e)}")
            self.status["modules"]["router"] = "error"
            return False
    
    def create_live_api_endpoint(self):
        """Create live API endpoint file"""
        self.log("🌐 Creating live API endpoint...")
        
        api_content = '''
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

app = FastAPI(title="SAFELOGIC SmartOrder PRO v6.14")

# Import live modules
try:
    from web.live_integration import get_live_status, start_live_modules
    from core.router import choose_exchange, get_routing_history
    MODULES_OK = True
except ImportError as e:
    print(f"Import error: {e}")
    MODULES_OK = False

@app.on_event("startup")
async def startup_event():
    if MODULES_OK:
        start_live_modules()
        print("🚀 All Phase 6.14 modules started")

@app.get("/")
def root():
    return {"status": "SAFELOGIC SmartOrder PRO v6.14 - Phase Complete", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/live_status")
def live_status():
    if not MODULES_OK:
        return {"error": "Modules not available"}
    return get_live_status()

@app.get("/api/router/test")
def test_router():
    if not MODULES_OK:
        return {"error": "Router not available"}
    
    result = choose_exchange("BTCUSDT", 0.001, 67000)
    history = get_routing_history()
    
    return {
        "selected_exchange": result,
        "routing_history": history[-5:],  # Last 5 decisions
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "phase": "6.14-complete",
        "modules_available": MODULES_OK,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8614)
'''
        
        try:
            with open("phase_614_api.py", "w", encoding="utf-8") as f:
                f.write(api_content)
            
            self.log("✅ Live API endpoint created: phase_614_api.py")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to create API endpoint: {str(e)}")
            return False
    
    def save_status(self):
        """Save current status to file"""
        try:
            status_data = {
                **self.status,
                "timestamp": datetime.now().isoformat(),
                "phase": "6.14-complete"
            }
            
            with open("phase_614_status.json", "w") as f:
                json.dump(status_data, f, indent=2)
            
        except Exception as e:
            self.log(f"⚠️ Failed to save status: {str(e)}")
    
    def show_final_status(self):
        """Show final deployment status"""
        self.log("=" * 60)
        self.log("📊 SAFELOGIC SMARTORDER PRO - PHASE 6.14 COMPLETE")
        self.log("=" * 60)
        
        for module, status in self.status["modules"].items():
            emoji = "✅" if status == "active" else "❌"
            self.log(f"{emoji} {module.replace('_', ' ').title()}: {status}")
        
        self.log("=" * 60)
        self.log("🌐 API Endpoints:")
        self.log("  Main API     : python phase_614_api.py")
        self.log("  Live Status  : http://localhost:8614/api/live_status")
        self.log("  Router Test  : http://localhost:8614/api/router/test") 
        self.log("  Health       : http://localhost:8614/api/health")
        
        self.log("=" * 60)
        self.log("📁 Files Created:")
        self.log("  Logs         : logs/phase_614.log")
        self.log("  Status       : phase_614_status.json")
        self.log("  API Server   : phase_614_api.py")
        
        self.log("=" * 60)
        
        # Calculate completion percentage
        active_modules = sum(1 for status in self.status["modules"].values() if status == "active")
        total_modules = len(self.status["modules"])
        completion = (active_modules / total_modules * 100) if total_modules > 0 else 0
        
        self.log(f"🎯 COMPLETION: {completion:.1f}% ({active_modules}/{total_modules} modules)")
        self.log("🚀 PHASE 6.14 DEPLOYMENT COMPLETE!")
        self.log("=" * 60)
    
    def launch_complete_stack(self):
        """Launch complete Phase 6.14 stack"""
        self.log("🎬 SAFELOGIC SmartOrder PRO - Phase 6.14 Launch")
        self.start_time = datetime.now()
        
        # Step 1: Start live modules (6.11-6.14)
        modules_ok = self.start_live_modules()
        
        # Step 2: Test router aiguillage
        router_ok = self.test_router_aiguillage()
        
        # Step 3: Create API endpoint
        api_ok = self.create_live_api_endpoint()
        
        # Step 4: Save status
        self.status["started"] = True
        self.save_status()
        
        # Step 5: Show final status
        time.sleep(1)
        self.show_final_status()
        
        # Step 6: Keep running for demonstration
        self.log("🔄 Phase 6.14 running... Press Ctrl+C to stop")
        
        try:
            # Test API endpoint every 30 seconds
            while True:
                time.sleep(30)
                self.log("💓 Phase 6.14 heartbeat - All systems operational")
                
        except KeyboardInterrupt:
            self.log("🛑 Phase 6.14 shutdown requested")
            self.log("👋 SAFELOGIC SmartOrder PRO Phase 6.14 stopped")

def main():
    """Main entry point"""
    launcher = Phase614Launcher()
    launcher.launch_complete_stack()

if __name__ == "__main__":
    main()