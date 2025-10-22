import os, time, psutil
from ai_core.ai_memory import AIMemory

APP_DIR = os.environ.get("APP_DIR", "/opt/smartorder-pro")
AI_DIR  = os.environ.get("AI_DIR", f"{APP_DIR}/ai_core")
LOG_DIR = os.environ.get("LOG_DIR", f"{APP_DIR}/logs")
os.makedirs(LOG_DIR, exist_ok=True)

MEM_PATH   = os.environ.get("AI_MEMORY_PATH", f"{AI_DIR}/ai_memory.json")
LOCKFILE   = os.environ.get("AI_PAUSE_LOCK", f"{AI_DIR}/PAUSED.lock")
CYCLE_SEC  = int(os.environ.get("LEARNING_CYCLE", "3600"))

LOG = f"{LOG_DIR}/ai_learner.log"

def log(msg: str):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def paused() -> bool:
    return os.path.exists(LOCKFILE)

def main():
    mem = AIMemory(MEM_PATH)
    log(f"🤖 AI Learner started | cycle={CYCLE_SEC}s | mem={MEM_PATH}")
    while True:
        if paused():
            log("⏸️  AI Learner paused (lock present). Sleeping 30s…")
            time.sleep(30)
            continue

        # Collecte minimale (CPU/RAM) – hooks d’extension pour signaux marché
        cpu = psutil.cpu_percent(interval=1.0)
        ram = psutil.virtual_memory().percent

        # Exemple d’adaptation : simple seuils -> écrit dans mémoire
        mem.update_metric("cpu", cpu)
        mem.update_metric("ram", ram)
        mem.append_note(f"Cycle ok: cpu={cpu} ram={ram}")

        log(f"✅ Learn cycle: cpu={cpu} ram={ram} -> mem updated")
        time.sleep(CYCLE_SEC)

if __name__ == "__main__":
    main()
