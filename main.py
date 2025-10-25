from fastapi import FastAPI
import os, psutil, json

app = FastAPI(title="SMARTORDER PRO AI v1.8-FINAL")

@app.get("/health")
def health():
    return {"ok": True, "ver": "1.8-final", "cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}

@app.get("/")
def index():
    return {"msg": "SMARTORDER PRO AI v1.8 is running!"}

# ==============================================================
# 🧩 SAFELOGIC Unified Monitor API – Phase 6
# ==============================================================

from fastapi import FastAPI
import psutil, subprocess, json, time

app = FastAPI()

@app.get("/api/system_status")
def system_status():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    services = {
        "smartorder-proxy": subprocess.getoutput("systemctl is-active smartorder-proxy.service"),
        "smartorder-websync-bridge": subprocess.getoutput("systemctl is-active smartorder-websync-bridge.service"),
        "smartorder-portal-v5": subprocess.getoutput("systemctl is-active smartorder-portal-v5.service"),
        "smartorder-watchdog": subprocess.getoutput("systemctl is-active smartorder-watchdog.service"),
    }

    return {
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "services": services,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/proxy_status")
def proxy_status():
    try:
        port_check = subprocess.getoutput("ss -tulnp | grep 8787 | wc -l")
        if int(port_check) > 0:
            return {"proxy": "🟢 actif", "port": 8787}
        else:
            return {"proxy": "🔴 inactif", "port": None}
    except Exception as e:
        return {"proxy": "⚠️ erreur", "error": str(e)}
