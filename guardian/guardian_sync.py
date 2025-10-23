#!/usr/bin/env python3
# =====================================================
# SAFELOGIC SMARTORDER PRO — GUARDIAN SYNC (PHASE 10)
# AutoSync GitHub <-> VPS + AutoRestore
# =====================================================
import os, time, subprocess, datetime

LOG_FILE = "/opt/smartorder/logs/guardian_sync.log"
REPO = "https://github.com/sazhjigbs/smartorder-pro-ai-v1.7.git"
LOCAL_PATH = "/opt/smartorder"
SLEEP = 1800  # 30 minutes

def log(msg):
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{now} {msg}\n")
    print(f"{now} {msg}")

def sync_git():
    try:
        if not os.path.exists(f"{LOCAL_PATH}/.git"):
            log("🧩 Initialisation du repo Git local…")
            subprocess.run(["git", "init"], cwd=LOCAL_PATH, check=True)
            subprocess.run(["git", "remote", "add", "origin", REPO], cwd=LOCAL_PATH, check=False)
        log("⬆️ Synchronisation vers GitHub…")
        subprocess.run(["git", "add", "."], cwd=LOCAL_PATH, check=False)
        subprocess.run(["git", "commit", "-m", f"AutoSync VPS {datetime.datetime.now()}"], cwd=LOCAL_PATH, check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=LOCAL_PATH, check=False)
        log("✅ Push vers GitHub terminé.")
    except Exception as e:
        log(f"⚠️ Erreur Sync GitHub : {e}")

def auto_restore():
    try:
        log("🔍 Vérification des services critiques…")
        for svc in ["smartorder-auto-executor", "smartorder-guardian"]:
            status = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
            if "inactive" in status.stdout or "failed" in status.stdout:
                log(f"⚠️ Service {svc} inactif — redémarrage.")
                subprocess.run(["systemctl", "restart", svc])
        log("✅ Vérification terminée.")
    except Exception as e:
        log(f"⚠️ Erreur auto_restore : {e}")

def main():
    log("=== 🛡️ Guardian Sync actif ===")
    while True:
        auto_restore()
        sync_git()
        log("💤 Pause 30 min avant prochaine vérification.")
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()
