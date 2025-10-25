#!/usr/bin/env python3
import os, time, subprocess, datetime

LOG_FILE = "/opt/smartorder/logs/guardian_sync.log"
SERVICES = ["smartorder-auto-executor.service", "smartorder-dashboard.service"]
REPO_PATH = "/opt/smartorder"

def log(msg):
    ts = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts} {msg}\n")

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        log(f"❌ {cmd} → {e.output.strip()}")
        return ""

def check_services():
    for svc in SERVICES:
        status = run(f"systemctl is-active {svc}").strip()
        if status != "active":
            log(f"⚠️ Service {svc} inactif — redémarrage")
            run(f"systemctl restart {svc}")

def sync_git():
    os.chdir(REPO_PATH)
    run("git add .")
    run('git commit -m "AutoSync from Guardian" || true')
    run("git pull origin main --rebase || true")
    run("git push origin main || true")

def main():
    while True:
        log("=== 🛡️ Guardian Sync actif ===")
        log("🔍 Vérification des services critiques…")
        check_services()
        log("✅ Vérification terminée.")
        log("⬆️ Synchronisation Git bidirectionnelle…")
        sync_git()
        log("✅ Sync & Guardian terminé. 💤 Pause 30 min avant prochaine vérification.")
        time.sleep(1800)

if __name__ == "__main__":
    main()
