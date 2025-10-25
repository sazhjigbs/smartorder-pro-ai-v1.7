import os, time, subprocess, datetime

LOG = "/opt/smartorder-pro/logs/guardian_diag.log"
SERVICES = [
    "smartorder-proxy.service",
    "smartorder-websync-bridge.service",
    "smartorder-portal-v5.service",
    "smartorder-watchdog.service"
]

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")

def check_service(service):
    status = subprocess.getoutput(f"systemctl is-active {service}")
    if status.strip() != "active":
        log(f"⚠️ {service} inactif — redémarrage...")
        subprocess.run(["systemctl", "restart", service])
        time.sleep(3)
        status2 = subprocess.getoutput(f"systemctl is-active {service}")
        if status2.strip() == "active":
            log(f"✅ {service} restauré avec succès.")
        else:
            log(f"❌ {service} échec de redémarrage ({status2}).")
    else:
        log(f"🟢 {service} OK")

if __name__ == "__main__":
    log("=== SAFELOGIC GUARDIAN DIAG INIT ===")
    while True:
        for svc in SERVICES:
            check_service(svc)
        time.sleep(60)
