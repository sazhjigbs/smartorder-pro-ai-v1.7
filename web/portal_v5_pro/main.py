from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import os, time, psutil

# imports locaux
from core.bybit_client import wallet_spot_balances, futures_positions, system_ping

app = FastAPI(title="SAFELOGIC SmartOrder PRO — Portal v5.1")

@app.get("/api/system_status")
def system_status():
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    return JSONResponse({{"cpu": cpu, "ram": ram, "uptime": time.strftime("%H:%M:%S", time.gmtime(time.time()-psutil.boot_time()))}})

@app.get("/api/spot_balances")
def api_spot():
    return JSONResponse(wallet_spot_balances())

@app.get("/api/futures_positions")
def api_futures():
    return JSONResponse(futures_positions())

@app.get("/api/ping")
def api_ping():
    return JSONResponse(system_ping())

@app.get("/", response_class=HTMLResponse)
def home():
    html = f"""
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SAFELOGIC Portal v5.1</title>
<style>
  :root {{ --bg:#0b1622; --card:#122036; --fg:#e8eef7; --muted:#9fb3c8; }}
  body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial; background:var(--bg); color:var(--fg); }}
  header {{ background:var(--card); padding:12px; text-align:center; font-weight:600; }}
  .wrap {{ max-width:1100px; margin:10px auto; padding:0 10px; }}
  .grid {{ display:grid; grid-template-columns:1fr; gap:10px; }}
  @media(min-width:900px) {{ .grid {{ grid-template-columns:1.2fr .8fr; }} }}
  .card {{ background:var(--card); border-radius:12px; padding:12px; box-shadow:0 2px 8px #0004; }}
  table {{ width:100%; border-collapse:collapse; }}
  th,td {{ padding:8px; border-bottom:1px solid #1b2d44; text-align:center; font-size:14px; }}
  th {{ color:var(--muted); font-weight:600; }}
  .ok {{ color:#4cff8f; font-weight:600; }}
  .muted {{ color:var(--muted); }}
  .row {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
  button {{ background:#1c2e4a; color:#e8eef7; border:none; padding:6px 10px; border-radius:8px; cursor:pointer; }}
  iframe {{ width:100%; height:420px; border:none; border-radius:12px; }}
</style>
<script>
async function loadAll(){{
  try {{
    const s = await fetch('/api/system_status').then(r=>r.json());
    document.getElementById('status').innerHTML = `🧠 IA | CPU: ${{s.cpu}}% · RAM: ${{s.ram}}% · Uptime: ${{s.uptime}}`;
  }} catch(e){{ document.getElementById('status').innerHTML = '⚠️ system_status KO'; }}

  try {{
    const a = await fetch('/api/spot_balances').then(r=>r.json());
    const rows = (a.spot||[]).map(x=>`<tr><td>${{x.asset||'-'}}</td><td>${{x.free||'-'}}</td></tr>`).join('') || "<tr><td colspan=2 class='muted'>Aucun solde</td></tr>";
    document.getElementById('spot').innerHTML = rows;
  }} catch(e){{ document.getElementById('spot').innerHTML = "<tr><td colspan=2>Erreur</td></tr>"; }}

    try {{
    const f = await fetch('/api/futures_positions').then(r=>r.json());
    const rows = (f.futures||[]).map(p=>`<tr><td>${{p.symbol||'-'}}</td><td>${{p.side||'-'}}</td><td>${{p.size||'-'}}</td><td>${{p.entryPrice||'-'}}</td><td>${{p.unrealPnl||'-'}}</td></tr>`).join('') || "<tr><td colspan=5 class='muted'>Aucune position</td></tr>";
    document.getElementById('futs').innerHTML = rows;
  }} catch(e){{ document.getElementById('futs').innerHTML = "<tr><td colspan=5>Erreur</td></tr>"; }}
}}
setInterval(loadAll, 5000);
window.onload = loadAll;
</script>
</head>
<body>
  <header>🚀 SAFELOGIC SmartOrder PRO — Dashboard v5.1</header>
  <div class="wrap">
    <div id="status" class="muted" style="margin:8px 0;">Chargement...</div>
    <div class="grid">
      <div class="card">
        <div class="row" style="justify-content:space-between;">
          <div style="font-weight:600;">📈 TradingView</div>
          <button onclick="loadAll()">🔁 Refresh</button>
        </div>
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BYBIT:BTCUSDT&interval=60&hidesidetoolbar=1&symboledit=1&saveimage=0&toolbarbg=f1f3f6&studies=[]&theme=dark"></iframe>
      </div>
      <div class="card">
        <div style="font-weight:600;">💰 Balances (Spot)</div>
        <table>
          <thead><tr><th>Asset</th><th>Free</th></tr></thead>
          <tbody id="spot"><tr><td colspan="2" class="muted">...</td></tr></tbody>
        </table>
      </div>
      <div class="card" style="grid-column:1/-1">
        <div style="font-weight:600;">⚙️ Positions (Futures)</div>
        <table>
          <thead><tr><th>Symbole</th><th>Side</th><th>Taille</th><th>Entrée</th><th>UPnL</th></tr></thead>
          <tbody id="futs"><tr><td colspan="5" class="muted">...</td></tr></tbody>
        </table>
      </div>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(html)
