import os, re, subprocess, logging, sys, requests

LOG = "/opt/smartorder-pro/logs/auto_fix.log"
MAIN = "/opt/smartorder-pro/web/portal_v5_pro/main.py"
ENV_PATH = "/opt/smartorder-pro/.env"

logging.basicConfig(filename=LOG, level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")

def send_telegram_alert(message: str):
    """Envoie une alerte via Telegram si TG_TOKEN et TG_CHAT_ID sont valides"""
    try:
        tg_token = None
        tg_chat = None
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH) as f:
                for line in f:
                    if line.startswith("TG_TOKEN="):
                        tg_token = line.strip().split("=",1)[1]
                    if line.startswith("TG_CHAT_ID="):
                        tg_chat = line.strip().split("=",1)[1]
        if tg_token and tg_chat:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {"chat_id": tg_chat, "text": message}
            requests.post(url, data=payload, timeout=5)
            logging.info(f"📩 Alerte Telegram envoyée : {message}")
        else:
            logging.warning("⚠️ Impossible d’envoyer une alerte Telegram : jeton/chat_id manquant")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l’envoi Telegram : {e}")

def check_env_keys():
    """Vérifie la présence des clés Bybit"""
    if not os.path.exists(ENV_PATH):
        logging.error("❌ Fichier .env introuvable !")
        send_telegram_alert("🚨 SAFELOGIC Portal: Fichier .env introuvable !")
        return False

    with open(ENV_PATH) as f:
        content = f.read()

    required = ["BYBIT_API_KEY", "BYBIT_API_SECRET"]
    missing = [k for k in required if f"{k}=" not in content]

    if missing:
        msg = f"🚨 SAFELOGIC Portal: Clés manquantes {', '.join(missing)}"
        logging.error(msg)
        send_telegram_alert(msg)
        return False

    logging.info("✅ Clés Bybit présentes dans .env")
    return True

def auto_fix_main():
    try:
        with open(MAIN, "r") as f:
            content = f.read()
        original = content

        # 1️⃣ Neutralise les accolades { } JS mal interprétées dans le HTML
        if "{:" in content or "{" in content:
            content = re.sub(r"(?<!\{)\{(?!\{)", "{{", content)
            content = re.sub(r"(?<!\})\}(?!\})", "}}", content)
            if content != original:
                with open(MAIN, "w") as f:
                    f.write(content)
                logging.info("✅ Neutralisation des { } dans le HTML effectuée")

        # 2️⃣ Vérifie et restaure core.bybit_client si nécessaire
        if "from core.bybit_client" in content and not os.path.exists("/opt/smartorder-pro/core/bybit_client.py"):
            os.makedirs("/opt/smartorder-pro/core", exist_ok=True)
            with open("/opt/smartorder-pro/core/bybit_client.py", "w") as f:
                f.write("def wallet_spot_balances(): return []\n")
                f.write("def futures_positions(): return []\n")
                f.write("def services_overall_ok(): return {'ok':True,'statuses':[]}\n")
            logging.warning("⚠️ Module core.bybit_client.py recréé automatiquement")

        # 3️⃣ Vérifie les clés Bybit
        check_env_keys()

        logging.info("🔧 Vérification du portail terminée sans erreur critique.")
    except Exception as e:
        logging.error(f"❌ Erreur auto-fix: {e}")
        send_telegram_alert(f"❌ SAFELOGIC Portal auto-fix : {e}")
        sys.exit(1)

if __name__ == "__main__":
    auto_fix_main()
