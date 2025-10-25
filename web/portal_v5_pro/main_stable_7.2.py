import sys, os, time, psutil, subprocess
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.append("/opt/smartorder-pro")

from core.pnl_live import start as pnl_start, get as pnl_get
from core.trust_memory_ai import start as trust_start, get as trust_get
from core.smart_execution import start as exec_start, get as exec_get
from core.market_context_ai import start as ctx_start, get as ctx_get

app = FastAPI(title="SAFELOGIC SmartOrder PRO — Dashboard v7.2-Pro+")

# === SYSTÈME ===
START_TIME = time.time()

def get_system_info():
    uptime = int(time.time() - START_TIME)
    return {
        "cpu": psutil.cpu_percent(interval=0.3),
        "ram": psutil.virtual_memory().percent,
        "uptime": f"{uptime//3600}h {(uptime%3600)//60}m"
    }

def get_guardian_logs():
    log_path = "/opt/smartorder-pro/logs/guardian.log"
    if not os.path.exists(log_path):
        return ["[Aucun log Guardian détecté]"]
    with open(log_path, "r") as f:
        lines = f.readlines()[-3:]
    return [l.strip() for l in lines if l.strip()]

def ping_latency():
    try:
        out = subprocess.check_output(["ping", "-c", "1", "-W", "1", "api.bybit.com"], text=True)
        for line in out.splitlines():
            if "time=" in line:
                return float(line.split("time=")[1].split(" ")[0])
    except Exception:
        return None

# === DÉMARRER LES MODULES IA ===
pnl_start()
trust_start()
exec_start()
ctx_start()

@app.get("/api/live_status")
def live_status():
    latency = ping_latency()
    return {
        "pnl": pnl_get(),
        "trust": trust_get(),
        "executions": exec_get(),
        "context": ctx_get(),
        "system": get_system_info(),
        "guardian": get_guardian_logs(),
        "latency": latency,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    html = f"""
    <html lang='fr'>
    <head>
        <meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>SAFELOGIC SmartOrder PRO — Dashboard v7.2</title>
        <style>
            body {{ margin:0; font-family:Arial; background:#0b1622; color:#fff; }}
            header {{ background:#122036; padding:12px; text-align:center; font-weight:bold; font-size:18px; }}
            #statusBar {{ background:#0f1d31; padding:8px; text-align:center; font-size:14px; }}
            .ok {{ color:#4cff8f; }}
            .warn {{ color:#ffcf33; }}
            iframe {{ width:100%; height:400px; border:none; }}
            table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
            th,td {{ padding:6px; border-bottom:1px solid #1b2d44; text-align:center; }}
            th {{ background:#122036; }}
            tr:hover {{ background:#162a45; }}
            .logbox {{ background:#0f1d31; padding:8px; margin:8px; border-radius:8px; font-family:monospace; font-size:13px; }}
        </style>
        <script>
            async function refreshAll(){{
                const live = await fetch('/api/live_status').then(r=>r.json());
                const pnl = live.pnl?.pnl || {{}};
                const trust = live.trust?.trust || {{}};
                const ctx = live.context?.context || {{}};
                const sys = live.system || {{}};
                const execs = live.executions?.executions || [];
                const guardian = live.guardian || [];
                const latency = live.latency || 0;

                document.getElementById('statusBar').innerHTML =
                    `🧠 <span class='ok'>IA active</span> | 🟢 Tous les services OK | CPU: ${'{'}sys.cpu{'}'}% | RAM: ${'{'}sys.ram{'}'}% | Uptime: ${'{'}sys.uptime{'}'} | Latence: ${'{'}latency{'}'} ms | Sentiment: ${'{'}ctx.sentiment || '-'{'}'} (${ '{'}ctx.fear_greed || '-'{'}'}) | ${'{'}live.timestamp{'}'}`;

                let tbl = "";
                tbl += `<tr><td>BTCUSDT</td><td>LONG</td><td>${'{'}trust.BTCUSDT || 0{'}'}%</td><td>${'{'}pnl.BTCUSDT || 0{'}'}%</td></tr>`;
                tbl += `<tr><td>ETHUSDT</td><td>SHORT</td><td>${'{'}trust.ETHUSDT || 0{'}'}%</td><td>${'{'}pnl.ETHUSDT || 0{'}'}%</td></tr>`;
                document.getElementById('tbl').innerHTML = tbl;

                let exhtml = "";
                execs.slice(-6).forEach(e =>
                    exhtml += `<tr><td>${'{'}e.symbol{'}'}</td><td>${'{'}e.side{'}'}</td><td>${'{'}e.size{'}'}</td><td>${'{'}e.entry{'}'}</td><td>${'{'}e.pnl{'}'}%</td><td>${'{'}e.time{'}'}</td></tr>`
                );
                document.getElementById('exe').innerHTML = exhtml || "<tr><td colspan='6'>Aucune exécution simulée...</td></tr>";

                document.getElementById('guardian').innerHTML = guardian.map(l => "📋 " + l).join("<br>");
            }}
            setInterval(refreshAll, 5000);
            window.onload = refreshAll;
        </script>
    </head>
    <body>
        <header>🚀 SAFELOGIC SmartOrder PRO — Dashboard v7.2-Pro+</header>
        <div id='statusBar'>Chargement du statut global...</div>
        <iframe src='https://s.tradingview.com/widgetembed/?frameElementId=tradingview'></iframe>

        <h3 style='padding:10px;'>📊 PNL & Confiance Live</h3>
        <table><thead><tr><th>Symbole</th><th>Type</th><th>Confiance</th><th>PNL</th></tr></thead>
        <tbody id='tbl'><tr><td colspan='4'>Chargement...</td></tr></tbody></table>

        <h3 style='padding:10px;'>⚙️ Exécutions (Spot + Futures)</h3>
        <table><thead><tr><th>Symbole</th><th>Type</th><th>Taille</th><th>Entrée</th><th>PNL</th><th>Heure</th></tr></thead>
        <tbody id='exe'><tr><td colspan='6'>Chargement...</td></tr></tbody></table>

        <h3 style='padding:10px;'>📋 Journal Guardian (3 dernières lignes)</h3>
        <div id='guardian' class='logbox'>Chargement...</div>
    </body></html>
    """
    return HTMLResponse(content=html)
