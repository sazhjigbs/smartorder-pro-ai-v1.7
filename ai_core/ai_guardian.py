import os, time, psutil, subprocess

APP_DIR = os.environ.get("APP_DIR", "/opt/smartorder-pro")
AI_DIR  = os.environ.get("AI_DIR", f"{APP_DIR}/ai_core")
LOG_DIR = os.environ.get("LOG_DIR", f"{APP_DIR}/logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOCKFILE   = os.path.join(AI_DIR, "PAUSED.lock")
LOG        = os.path.join(LOG_DIR, "ai_guardian.log")

CPU_HI = float(os.environ.get("AI_CPU_HIGH", "85"))
CPU_LO = float(os.environ.get("AI_CPU_LOW",  "60"))
RAM_HI = float(os.environ.get("AI_RAM_HIGH", "80"))

def log(msg: str):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def pause():
    if not os.path.exists(LOCKFILE):
        open(LOCKFILE, "w").close()
        log("⚠️  Guardian: created PAUSE lock")

def resume():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        log("✅ Guardian: removed PAUSE lock")

def restart_unit(unit):
    try:
        subprocess.run(["systemctl", "restart", unit], check=False)
        log(f"🔁 Guardian: restarted {unit}")
    except Exception as e:
        log(f"❌ Guardian: restart error {unit}: {e}")

def main():
    log("🛡️ AI Guardian started")
    while True:
        cpu = psutil.cpu_percent(interval=2.0)
        ram = psutil.virtual_memory().percent
        if cpu >= CPU_HI or ram >= RAM_HI:
            pause()
        elif cpu <= CPU_LO and ram < RAM_HI:
            resume()
        time.sleep(8)

if __name__ == "__main__":
    main()
