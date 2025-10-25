import sys, os, time, psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

# S'assurer que le répertoire parent est dans le path
sys.path.append("/opt/smartorder-pro")

# Importer les modules IA
from core.pnl_live import start as pnl_start, get as pnl_get
from core.trust_memory_ai import start as trust_start, get as trust_get
from core.smart_execution import start as exec_start, get as exec_get
from core.market_context_ai import start as ctx_start, get as ctx_get

app = FastAPI(title="SAFELOGIC SmartOrder PRO — Dashboard v7.1-SafeHTML")

# === MÉTRIQUES SYSTÈME ===
def get_system_metrics():
    """Retourne CPU et RAM en %"""
    return {
        "cpu": psutil.cpu_percent(interval=0.5),
        "ram": psutil.virtual_memory().percent
    }

# === DÉMARRER LES MODULES IA ===
pnl_start()
trust_start()
exec_start()
ctx_start()

# === API LIVE STATUS ===
@app.get("/api/live_status")
def live_status():
    return {
        "pnl": pnl_get(),
        "trust": trust_get(),
        "executions": exec_get(),
        "context": ctx_get(),
        "system": get_system_metrics(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# === DASHBOARD HTML ===
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    html = f"""
    <html lang='fr'>
    <head>
        <meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>SAFELOGIC SmartOrder PRO — Dashboard v7.1</title>
        <style>
            body {{ margin:0; font-family:Arial; background:#0b1622; color:#fff; }}
            header {{ background:#122036; padding:12px; text-align:center; font-weight:bold; font-size:18px; }}
            table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
            th,td {{ padding:6px; border-bottom:1px solid #1b2d44; text-align:center; }}
            th {{ background:#122036; }}
            tr:hover {{ background:#162a45; }}
            #statusBar {{ background:#0f1d31; padding:8px; text-align:center; font-size:14px; }}
            iframe {{ width:100%; height:400px; border:none; margin-top:6px; }}
            .ok {{ color:#4cff8f; }}
            .warn {{ color:#ffcf33; }}
        </style>
        <script>
            async function refreshAll(){{
                const live = await fetch('/api/live_status').then(r=>r.json());
                const pnl = live.pnl?.pnl || {{}};
                const trust = live.trust?.trust || {{}};
                const ctx = live.context?.context || {{}};
                const sys = live.system || {{}};
                const execs = live.executions?.executions || [];

                document.getElementById('statusBar').innerHTML =
                    `🧠 <span class='ok'>IA active</span> | CPU: ${'{'}sys.cpu{'}'}% RAM: ${'{'}sys.ram{'}'}% | ` +
                    `Sentiment: ${'{'}ctx.sentiment || '-'{'}'} (${ '{'}ctx.fear_greed || '-'{'}'}) | ` +
                    `BTC: ${'{'}trust.BTCUSDT || 0{'}'}% | ETH: ${'{'}trust.ETHUSDT || 0{'}'}% | ` +
                    `${'{'}live.timestamp{'}'}`;

                document.getElementById('tbl').innerHTML = `
                    <tr><td>BTCUSDT</td><td>LONG</td><td>${'{'}trust.BTCUSDT || 0{'}'}%</td><td>${'{'}pnl.BTCUSDT || 0{'}'}%</td></tr>
                    <tr><td>ETHUSDT</td><td>SHORT</td><td>${'{'}trust.ETHUSDT || 0{'}'}%</td><td>${'{'}pnl.ETHUSDT || 0{'}'}%</td></tr>`;

                let exhtml = '';
                execs.slice(-5).forEach(e =>
                    exhtml += `<tr><td>${'{'}e.symbol{'}'}</td><td>${'{'}e.side{'}'}</td><td>${'{'}e.size{'}'}</td><td>${'{'}e.entry{'}'}</td><td>${'{'}e.pnl{'}'}%</td><td>${'{'}e.time{'}'}</td></tr>`
                );
                document.getElementById('exe').innerHTML = exhtml || "<tr><td colspan='6'>Aucune exécution simulée...</td></tr>";
            }}
            setInterval(refreshAll, 10000);
            window.onload = refreshAll;
        </script>
    </head>
    <body>
        <header>🚀 SAFELOGIC SmartOrder PRO — Dashboard v7.1</header>
        <div id='statusBar'>Chargement du statut IA...</div>
        <iframe src='https://s.tradingview.com/widgetembed/?frameElementId=tradingview'></iframe>
        <h3 style='padding:10px;'>📊 PNL & Confiance Live</h3>
        <table><thead><tr><th>Symbole</th><th>Type</th><th>Confiance</th><th>PNL</th></tr></thead>
        <tbody id='tbl'><tr><td colspan='4'>Chargement...</td></tr></tbody></table>
        <h3 style='padding:10px;'>⚙️ Exécutions simulées</h3>
        <table><thead><tr><th>Symbole</th><th>Type</th><th>Taille</th><th>Entrée</th><th>PNL</th><th>Heure</th></tr></thead>
        <tbody id='exe'><tr><td colspan='6'>Chargement...</td></tr></tbody></table>
    </body></html>
    """
    return HTMLResponse(content=html)
