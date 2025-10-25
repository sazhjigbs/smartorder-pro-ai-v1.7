import os, time, psutil, subprocess, datetime

SERVICE = "smartorder-websync-bridge.service"
LOGFILE = "/opt/smartorder-pro/logs/watchdog.log"

def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")

def is_running():
    for p in psutil.process_iter(attrs=["cmdline"]):
        if "websync_bridge.py" in " ".join(p.info["cmdline"]):
            return True
    return False

def check_activity():
    log_path = "/opt/smartorder-pro/logs/websync_bridge.log"
    if not os.path.exists(log_path): return False
    mtime = os.path.getmtime(log_path)
    # Dernière activité il y a plus de 30s ? => considérer comme figé
    return (time.time() - mtime) < 30

def restart_service():
    subprocess.run(["systemctl", "restart", SERVICE], stdout=subprocess.DEVNULL)
    log(f"⚠️ Redémarrage automatique du service {SERVICE}")

if __name__ == "__main__":
    log("🚀 Watchdog Bridge démarré")
    while True:
        if not is_running() or not check_activity():
            restart_service()
        time.sleep(10)
# SAFELOGIC PATCH – Phase 5 Proxy monitoring
if not any("smartorder-proxy.service" in s for s in open(LOGFILE).read().splitlines()):
    subprocess.run(["systemctl", "restart", "smartorder-proxy.service"])
