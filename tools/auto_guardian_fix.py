#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
SAFELOGIC SmartOrder Auto-Guardian PRO
Version : 1.8-FINAL
"""

import os
import subprocess
import time
import datetime
import logging
import requests

LOG_PATH = "/opt/smartorder-pro/logs/auto_guardian_fix.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

def log(msg):
    print(msg)
    logging.info(msg)

def send_telegram(message):
    try:
        token = os.getenv("TG_TOKEN")
        chat_id = os.getenv("TG_CHAT_ID")
        if token and chat_id:
            requests.get(
                f"https://api.telegram.org/bot{token}/sendMessage",
                params={"chat_id": chat_id, "text": message}
            )
    except Exception as e:
        logging.error(f"Erreur Telegram: {e}")

def fix_portal_structure():
    try:
        web_dir = "/opt/smartorder-pro/web"
        portal_dir = f"{web_dir}/portal_v5_pro"
        init_files = [f"{web_dir}/__init__.py", f"{portal_dir}/__init__.py"]

        os.makedirs(portal_dir, exist_ok=True)
        for file in init_files:
            if not os.path.exists(file):
                with open(file, "w") as f:
                    f.write("# Auto-created by SAFELOGIC Guardian\n")
                log(f"🧩 Fichier créé : {file}")

        log("🧩 Correction appliquée : modules init vérifiés.")
    except Exception as e:
        log(f"❌ Erreur fix_portal_structure: {e}")
        send_telegram(f"⚠️ Erreur fix_portal_structure: {e}")

def check_bybit_keys():
    env_file = "/opt/smartorder-pro/.env"
    try:
        with open(env_file, "r") as f:
            content = f.read()
        if "BYBIT_API_KEY=" in content and "BYBIT_API_SECRET=" in content:
            log("✅ Clés Bybit présentes dans .env")
            return True
        else:
            log("❌ Clés Bybit absentes dans .env")
            send_telegram("⚠️ Clés Bybit absentes dans .env !")
            return False
    except Exception as e:
        log(f"❌ Erreur lecture .env: {e}")
        send_telegram(f"⚠️ Erreur lecture .env: {e}")
        return False

def sync_with_github():
    try:
        repo = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")
        autosync = os.getenv("AUTO_SYNC_ENABLED", "False").lower() == "true"

        if autosync and repo:
            log("🪶 AutoSync GitHub activé, synchronisation en cours...")
            subprocess.run(["git", "fetch", "origin"], cwd="/opt/smartorder-pro", check=False)
            subprocess.run(["git", "reset", "--hard", f"origin/{branch}"], cwd="/opt/smartorder-pro", check=False)
            log(f"✅ Synchronisation GitHub effectuée à {datetime.datetime.now()}")
            send_telegram(f"✅ AutoSync GitHub réussi ({branch}) à {datetime.datetime.now()}")
        else:
            log("⚠️ AutoSync désactivé ou configuration incomplète.")
    except Exception as e:
        log(f"❌ Erreur AutoSync GitHub : {e}")
        send_telegram(f"❌ Erreur AutoSync GitHub : {e}")

def restart_services():
    try:
        subprocess.run(["systemctl", "restart", "smartorder-portal-v5.service"], check=False)
        subprocess.run(["systemctl", "restart", "smartorder-websync-bridge.service"], check=False)
        log("🔁 Tous les services SmartOrder redémarrés.")
    except Exception as e:
        log(f"❌ Erreur restart_services: {e}")
        send_telegram(f"⚠️ Erreur restart_services: {e}")

if __name__ == "__main__":
    log("🛡️ Lancement du correcteur global SAFELOGIC Guardian...")
    send_telegram("🛡️ SAFELOGIC Auto-Guardian lancé sur VPS.")

    while True:
        fix_portal_structure()
        check_bybit_keys()
        sync_with_github()
        restart_services()
        time.sleep(int(os.getenv("SYNC_INTERVAL", "300")))
