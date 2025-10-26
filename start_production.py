#!/usr/bin/env python3
"""
🚀 SAFELOGIC SmartOrder PRO — Production Startup Script
Lance tous les modules en mode production pour transition Phase 4 → Phase 5
"""

import os
import time
import subprocess
import threading
from datetime import datetime

class ProductionLauncher:
    def __init__(self):
        self.processes = {}
        self.is_running = True
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def start_module(self, name, script_path, delay=0):
        """Lance un module en arrière-plan"""
        if delay > 0:
            time.sleep(delay)
            
        try:
            self.log(f"Démarrage {name}...")
            
            # Démarrer le processus
            process = subprocess.Popen([
                "python", script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes[name] = process
            self.log(f"✅ {name} démarré (PID: {process.pid})")
            
        except Exception as e:
            self.log(f"❌ Erreur démarrage {name}: {str(e)}")
    
    def monitor_processes(self):
        """Surveille les processus et redémarre si nécessaire"""
        while self.is_running:
            try:
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:  # Processus terminé
                        self.log(f"🔄 {name} s'est arrêté, redémarrage...")
                        
                        # Redémarrer selon le module
                        if name == "Portal":
                            self.start_module_thread("Portal", "web/portal_v5_pro/main.py")
                        elif name == "Self-Learning":
                            self.start_module_thread("Self-Learning", "ai_core/self_learning_loop.py")
                        elif name == "Git Sync":
                            self.start_module_thread("Git Sync", "tools/git_push_guardian.py")
                        elif name == "Execution Bridge":
                            self.start_module_thread("Execution Bridge", "executor/execution_bridge_clean.py")
                
                time.sleep(30)  # Vérifier toutes les 30s
                
            except Exception as e:
                self.log(f"❌ Erreur monitoring: {str(e)}")
                time.sleep(10)
    
    def start_module_thread(self, name, script_path, delay=0):
        """Lance un module dans un thread séparé"""
        thread = threading.Thread(
            target=self.start_module,
            args=(name, script_path, delay),
            daemon=True
        )
        thread.start()
    
    def launch_production_stack(self):
        """Lance la stack complète de production"""
        self.log("🚀 DÉMARRAGE PRODUCTION SAFELOGIC SMARTORDER PRO")
        self.log("Version: v1.8-FINAL → Phase 5 ADAPTIVE")
        
        # 1. Auto-Sync GitHub (priorité)
        self.start_module_thread("Git Sync", "tools/git_push_guardian.py", delay=2)
        
        # 2. Self-Learning Loop (cœur IA)
        self.start_module_thread("Self-Learning", "ai_core/self_learning_loop.py", delay=5)
        
        # 3. Portal Web (interface)
        self.start_module_thread("Portal", "web/portal_v5_pro/main.py", delay=8)
        
        # 4. Execution Bridge (trading)
        self.start_module_thread("Execution Bridge", "executor/execution_bridge_clean.py", delay=12)
        
        # 5. Notification de démarrage
        time.sleep(15)
        try:
            from tools.guardian_notify import notify_system_start
            notify_system_start()
        except:
            self.log("⚠️ Notification Telegram non disponible")
        
        # 6. Lancer le monitoring
        self.log("🛡️ Démarrage du monitoring continu...")
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # 7. Rapport de statut
        time.sleep(5)
        self.show_status()
        
        # 8. Boucle principale
        try:
            while self.is_running:
                time.sleep(60)  # Status toutes les minutes
                self.show_brief_status()
        except KeyboardInterrupt:
            self.stop_all()
    
    def show_status(self):
        """Affiche le statut complet"""
        self.log("=" * 60)
        self.log("📊 STATUT SMARTORDER PRO")
        self.log("=" * 60)
        
        for name, process in self.processes.items():
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            pid = process.pid if process.poll() is None else "N/A"
            self.log(f"{name:20s} : {status} (PID: {pid})")
        
        self.log("=" * 60)
        self.log("🌐 Endpoints actifs:")
        self.log("  Portal Web       : http://localhost:8555/")
        self.log("  API Status       : http://localhost:8555/api/system_status")
        self.log("  Logs Bridge      : logs/execution_bridge.log")
        self.log("  Logs Git Sync    : logs/git_sync.log")
        self.log("=" * 60)
    
    def show_brief_status(self):
        """Statut bref pour monitoring"""
        running_count = sum(1 for p in self.processes.values() if p.poll() is None)
        total_count = len(self.processes)
        
        if running_count == total_count:
            self.log(f"✅ Tous modules actifs ({running_count}/{total_count})")
        else:
            self.log(f"⚠️ Modules: {running_count}/{total_count} actifs")
    
    def stop_all(self):
        """Arrête tous les processus"""
        self.log("🛑 Arrêt de tous les modules...")
        self.is_running = False
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    process.terminate()
                    self.log(f"🛑 {name} arrêté")
            except:
                pass
        
        self.log("👋 SmartOrder PRO arrêté proprement")

def main():
    """Point d'entrée principal"""
    launcher = ProductionLauncher()
    
    try:
        launcher.launch_production_stack()
    except KeyboardInterrupt:
        launcher.stop_all()
    except Exception as e:
        launcher.log(f"💥 Erreur fatale: {str(e)}")
        launcher.stop_all()

if __name__ == "__main__":
    main()