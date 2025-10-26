#!/usr/bin/env python3
"""
🚀 SAFELOGIC SmartOrder PRO — Unified Dashboard v6.0
Dashboard complet avec Execution Engine intégrée
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, time, psutil, sys

# Import auth
try:
    from web.portal_v5_pro.auth import require_auth
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False
    def require_auth(): return None

# Add project root to path
sys.path.insert(0, '/opt/smartorder-pro')

# Imports locaux
from core.bybit_client import wallet_spot_balances, futures_positions, system_ping

# Import Execution Engine
try:
    from core.execution_engine import get_engine
    EXECUTION_ENABLED = True
except ImportError:
    EXECUTION_ENABLED = False
    print("⚠️ Execution Engine not available")

# Import PNL Live & Signal Memory APIs
try:
    from web.portal_v5_pro.api_pnl_live import router as pnl_router
    from web.portal_v5_pro.api_signal_memory import router as signal_router
    PNL_ENABLED = True
except ImportError:
    PNL_ENABLED = False

# Import NEW APIs (v6.0 features)
try:
    from web.portal_v5_pro.api_auth import router as auth_router
    from web.portal_v5_pro.api_charts import router as charts_router
    from web.portal_v5_pro.api_alerts import router as alerts_router
    NEW_FEATURES_ENABLED = True
except ImportError as e:
    print(f"⚠️ New features not available: {e}")
    NEW_FEATURES_ENABLED = False

app = FastAPI(title="SAFELOGIC SmartOrder PRO — Unified Dashboard v6.0")

# Templates for new features
templates = Jinja2Templates(directory="web/portal_v5_pro/templates")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="web/portal_v5_pro/static"), name="static")
except:
    pass

# Include routers
if PNL_ENABLED:
    app.include_router(pnl_router)
    app.include_router(signal_router)

if NEW_FEATURES_ENABLED:
    app.include_router(auth_router)
    app.include_router(charts_router)
    app.include_router(alerts_router)

# ========== SYSTEM APIs ==========

@app.get("/api/system_status")
def system_status():
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return JSONResponse({
        "cpu": cpu, 
        "ram": ram,
        "disk": disk,
        "uptime": time.strftime("%H:%M:%S", time.gmtime(time.time()-psutil.boot_time()))
    })

@app.get("/api/spot_balances")
def api_spot():
    return JSONResponse(wallet_spot_balances())

@app.get("/api/futures_positions")
def api_futures():
    return JSONResponse(futures_positions())

@app.get("/api/ping")
def api_ping():
    return JSONResponse(system_ping())

# ========== EXECUTION ENGINE APIs ==========

@app.post("/api/execution/split-order")
async def split_order_api(data: dict):
    """Split un ordre en plusieurs"""
    if not EXECUTION_ENABLED:
        return JSONResponse({"error": "Execution Engine not enabled"}, status_code=503)
    
    engine = get_engine()
    splits = engine.split_order(
        symbol=data['symbol'],
        side=data['side'],
        total_quantity=data['total_quantity'],
        price=data['price'],
        num_splits=data.get('num_splits', 3),
        delay_seconds=data.get('delay_seconds', 2)
    )
    return JSONResponse({"success": True, "splits": splits})

@app.post("/api/execution/partial-close")
async def partial_close_api(data: dict):
    """Fermeture partielle"""
    if not EXECUTION_ENABLED:
        return JSONResponse({"error": "Execution Engine not enabled"}, status_code=503)
    
    engine = get_engine()
    result = engine.partial_close(
        symbol=data['symbol'],
        position_size=data['position_size'],
        close_percentage=data['close_percentage'],
        current_price=data['current_price']
    )
    return JSONResponse({"success": True, "partial_close": result})

@app.post("/api/execution/trailing-stop/setup")
async def trailing_stop_setup_api(data: dict):
    """Configure trailing stop"""
    if not EXECUTION_ENABLED:
        return JSONResponse({"error": "Execution Engine not enabled"}, status_code=503)
    
    engine = get_engine()
    trail = engine.setup_trailing_stop(
        symbol=data['symbol'],
        side=data['side'],
        entry_price=data['entry_price'],
        trail_percent=data['trail_percent'],
        current_price=data.get('current_price')
    )
    return JSONResponse({"success": True, "trailing_stop": trail})

@app.get("/api/execution/trailing-stops")
async def get_all_trailing_stops():
    """Liste tous les trailing stops"""
    if not EXECUTION_ENABLED:
        return JSONResponse({"error": "Execution Engine not enabled"}, status_code=503)
    
    engine = get_engine()
    stops = engine.get_all_trailing_stops()
    return JSONResponse({"success": True, "trailing_stops": stops, "count": len(stops)})

@app.delete("/api/execution/trailing-stop/{symbol}")
async def cancel_trailing_stop(symbol: str):
    """Annule trailing stop"""
    if not EXECUTION_ENABLED:
        return JSONResponse({"error": "Execution Engine not enabled"}, status_code=503)
    
    engine = get_engine()
    success = engine.cancel_trailing_stop(symbol)
    return JSONResponse({"success": success})

@app.get("/api/execution/health")
async def execution_health():
    """Health check execution engine"""
    if not EXECUTION_ENABLED:
        return JSONResponse({"status": "disabled", "execution_engine": False})
    
    engine = get_engine()
    return JSONResponse({
        "status": "healthy",
        "execution_engine": True,
        "active_trailing_stops": len(engine.get_all_trailing_stops()),
        "active_split_orders": len(engine.split_orders)
    })

# ========== UNIFIED DASHBOARD ==========

@app.get("/", response_class=HTMLResponse)
def unified_dashboard(username: str = Depends(require_auth) if AUTH_ENABLED else None):
    html = """
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SAFELOGIC SmartOrder PRO v6.0</title>
<style>
  :root { --bg:#0a0e1a; --card:#1a1f35; --card-hover:#222842; --fg:#e8eef7; --muted:#8a95a8; --primary:#4c9aff; --success:#4cff8f; --danger:#ff6b6b; --warning:#ffd93d; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif; background:var(--bg); color:var(--fg); }
  header { background:linear-gradient(135deg,#1a1f35,#2a3555); padding:16px 24px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 4px 12px #0004; }
  .logo { font-size:24px; font-weight:700; background:linear-gradient(135deg,var(--primary),var(--success)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .status-bar { display:flex; gap:20px; font-size:13px; }
  .status-item { display:flex; align-items:center; gap:6px; }
  .pulse { width:8px; height:8px; border-radius:50%; background:var(--success); animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  
  .container { max-width:1400px; margin:20px auto; padding:0 20px; }
  .tabs { display:flex; gap:8px; margin-bottom:20px; background:var(--card); padding:8px; border-radius:12px; }
  .tab { padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:500; transition:all 0.2s; border:none; background:transparent; color:var(--muted); }
  .tab:hover { background:var(--card-hover); color:var(--fg); }
  .tab.active { background:var(--primary); color:#fff; }
  
  .tab-content { display:none; }
  .tab-content.active { display:block; animation:fadeIn 0.3s; }
  @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
  
  .grid { display:grid; gap:16px; }
  .grid-2 { grid-template-columns:repeat(auto-fit,minmax(400px,1fr)); }
  .grid-3 { grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); }
  
  .card { background:var(--card); border-radius:16px; padding:20px; box-shadow:0 2px 8px #0003; transition:transform 0.2s,box-shadow 0.2s; }
  .card:hover { transform:translateY(-2px); box-shadow:0 4px 16px #0004; }
  .card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
  .card-title { font-size:18px; font-weight:600; display:flex; align-items:center; gap:8px; }
  
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th,td { padding:12px 8px; border-bottom:1px solid #2a3555; text-align:left; }
  th { color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; }
  
  .badge { display:inline-block; padding:4px 12px; border-radius:6px; font-size:12px; font-weight:600; }
  .badge-success { background:#4cff8f22; color:var(--success); }
  .badge-danger { background:#ff6b6b22; color:var(--danger); }
  .badge-warning { background:#ffd93d22; color:var(--warning); }
  .badge-primary { background:#4c9aff22; color:var(--primary); }
  
  .btn { padding:10px 20px; border-radius:8px; border:none; font-weight:600; cursor:pointer; transition:all 0.2s; font-size:14px; }
  .btn-primary { background:var(--primary); color:#fff; }
  .btn-success { background:var(--success); color:#0a0e1a; }
  .btn-danger { background:var(--danger); color:#fff; }
  .btn:hover { transform:translateY(-2px); box-shadow:0 4px 12px #0004; }
  .btn:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
  
  .input-group { margin-bottom:16px; }
  .input-group label { display:block; margin-bottom:6px; font-size:13px; font-weight:600; color:var(--muted); }
  .input-group input, .input-group select { width:100%; padding:10px 12px; background:var(--bg); border:1px solid #2a3555; border-radius:8px; color:var(--fg); font-size:14px; }
  .input-group input:focus, .input-group select:focus { outline:none; border-color:var(--primary); }
  
  .stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
  .stat-card { background:var(--bg); padding:16px; border-radius:12px; text-align:center; }
  .stat-value { font-size:28px; font-weight:700; margin-bottom:4px; }
  .stat-label { font-size:12px; color:var(--muted); text-transform:uppercase; }
  
  iframe { width:100%; height:420px; border:none; border-radius:12px; background:var(--bg); }
</style>
</head>
<body>
  <header>
    <div class="logo">🚀 SAFELOGIC SmartOrder PRO v6.0</div>
    <div class="status-bar">
      <div class="status-item"><div class="pulse"></div><span id="status-text">Loading...</span></div>
      <div class="status-item">CPU: <strong id="cpu">-</strong>%</div>
      <div class="status-item">RAM: <strong id="ram">-</strong>%</div>
    </div>
  </header>

  <div class="container">
    <div class="tabs">
      <button class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
      <button class="tab" onclick="switchTab('positions')">💼 Positions</button>
      <button class="tab" onclick="switchTab('execution')">⚡ Execution</button>
      <button class="tab" onclick="switchTab('pnl')">📈 PNL Live</button>
      <button class="tab" onclick="switchTab('signals')">🎯 Signals</button>
      <button class="tab" onclick="window.location.href='/analytics'">📊 Analytics</button>
      <button class="tab" onclick="window.location.href='/login'">🔐 Login</button>
    </div>

    <!-- TAB: Dashboard -->
    <div id="tab-dashboard" class="tab-content active">
      <div class="grid grid-2">
        <div class="card">
          <div class="card-header">
            <div class="card-title">📈 TradingView</div>
            <button class="btn btn-primary" onclick="loadAll()">🔄 Refresh</button>
          </div>
          <iframe src="https://s.tradingview.com/widgetembed/?symbol=BYBIT:BTCUSDT&interval=60&hidesidetoolbar=1&symboledit=1&saveimage=0&toolbarbg=f1f3f6&studies=[]&theme=dark"></iframe>
        </div>
        <div class="card">
          <div class="card-title">💰 Spot Balances</div>
          <table>
            <thead><tr><th>Asset</th><th>Free</th><th>Locked</th></tr></thead>
            <tbody id="spot-table"><tr><td colspan="3" style="text-align:center;color:var(--muted)">Loading...</td></tr></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB: Positions -->
    <div id="tab-positions" class="tab-content">
      <div class="card">
        <div class="card-title">⚙️ Futures Positions</div>
        <table>
          <thead><tr><th>Symbol</th><th>Side</th><th>Size</th><th>Entry</th><th>UPnL</th><th>Actions</th></tr></thead>
          <tbody id="positions-table"><tr><td colspan="6" style="text-align:center;color:var(--muted)">Loading...</td></tr></tbody>
        </table>
      </div>
    </div>

    <!-- TAB: Execution -->
    <div id="tab-execution" class="tab-content">
      <div class="grid grid-2">
        <div class="card">
          <div class="card-title">📊 Split Order</div>
          <div class="input-group">
            <label>Symbol</label>
            <input type="text" id="split-symbol" placeholder="BTCUSDT" value="BTCUSDT">
          </div>
          <div class="input-group">
            <label>Side</label>
            <select id="split-side">
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          <div class="input-group">
            <label>Total Quantity</label>
            <input type="number" id="split-qty" placeholder="0.003" step="0.001">
          </div>
          <div class="input-group">
            <label>Price</label>
            <input type="number" id="split-price" placeholder="67000" step="0.01">
          </div>
          <div class="input-group">
            <label>Number of Splits (2-10)</label>
            <input type="number" id="split-num" placeholder="3" value="3" min="2" max="10">
          </div>
          <button class="btn btn-primary" onclick="createSplitOrder()">Create Split Order</button>
        </div>

        <div class="card">
          <div class="card-title">🎯 Trailing Stop</div>
          <div class="input-group">
            <label>Symbol</label>
            <input type="text" id="trail-symbol" placeholder="BTCUSDT" value="BTCUSDT">
          </div>
          <div class="input-group">
            <label>Side</label>
            <select id="trail-side">
              <option value="LONG">LONG</option>
              <option value="SHORT">SHORT</option>
            </select>
          </div>
          <div class="input-group">
            <label>Entry Price</label>
            <input type="number" id="trail-entry" placeholder="67000" step="0.01">
          </div>
          <div class="input-group">
            <label>Trail Percent (%)</label>
            <input type="number" id="trail-pct" placeholder="2.0" value="2.0" step="0.1">
          </div>
          <button class="btn btn-success" onclick="setupTrailingStop()">Setup Trailing Stop</button>
        </div>
      </div>

      <div class="card" style="margin-top:16px">
        <div class="card-header">
          <div class="card-title">🔴 Active Trailing Stops</div>
          <button class="btn btn-primary" onclick="loadTrailingStops()">🔄 Refresh</button>
        </div>
        <div id="trailing-stops-list" style="color:var(--muted);text-align:center;padding:20px">No active trailing stops</div>
      </div>
    </div>

    <!-- TAB: PNL -->
    <div id="tab-pnl" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div class="card-title">📈 PNL Summary</div>
          <button class="btn btn-primary" onclick="loadPNL()">🔄 Refresh</button>
        </div>
        <div id="pnl-summary" style="color:var(--muted);text-align:center;padding:20px">Loading PNL data...</div>
      </div>
    </div>

    <!-- TAB: Signals -->
    <div id="tab-signals" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div class="card-title">🎯 Signal Trust Score</div>
          <button class="btn btn-primary" onclick="loadSignals()">🔄 Refresh</button>
        </div>
        <div id="signals-data" style="color:var(--muted);text-align:center;padding:20px">Loading signals...</div>
      </div>
    </div>
  </div>

<script>
let currentTab = 'dashboard';

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById(`tab-${tab}`).classList.add('active');
  
  if(tab === 'execution') loadTrailingStops();
  if(tab === 'pnl') loadPNL();
  if(tab === 'signals') loadSignals();
}

async function loadAll() {
  try {
    const s = await fetch('/api/system_status').then(r=>r.json());
    document.getElementById('status-text').textContent = `Uptime: ${s.uptime}`;
    document.getElementById('cpu').textContent = s.cpu.toFixed(1);
    document.getElementById('ram').textContent = s.ram.toFixed(1);
  } catch(e) { console.error('Status error:', e); }

  try {
    const a = await fetch('/api/spot_balances').then(r=>r.json());
    const rows = (a.spot||[]).map(x=>`<tr><td>${x.asset||'-'}</td><td>${x.free||'-'}</td><td>${x.locked||'0'}</td></tr>`).join('') || "<tr><td colspan=3 style='text-align:center;color:var(--muted)'>No balances</td></tr>";
    document.getElementById('spot-table').innerHTML = rows;
  } catch(e) { console.error('Spot error:', e); }

  try {
    const f = await fetch('/api/futures_positions').then(r=>r.json());
    const rows = (f.futures||[]).map(p=>`<tr><td>${p.symbol||'-'}</td><td><span class="badge badge-${p.side==='LONG'?'success':'danger'}">${p.side||'-'}</span></td><td>${p.size||'-'}</td><td>${p.entryPrice||'-'}</td><td style="color:${parseFloat(p.unrealPnl)>=0?'var(--success)':'var(--danger)'}">${p.unrealPnl||'-'}</td><td><button class="btn btn-danger" style="padding:4px 12px">Close</button></td></tr>`).join('') || "<tr><td colspan=6 style='text-align:center;color:var(--muted)'>No positions</td></tr>";
    document.getElementById('positions-table').innerHTML = rows;
  } catch(e) { console.error('Positions error:', e); }
}

async function createSplitOrder() {
  const data = {
    symbol: document.getElementById('split-symbol').value,
    side: document.getElementById('split-side').value,
    total_quantity: parseFloat(document.getElementById('split-qty').value),
    price: parseFloat(document.getElementById('split-price').value),
    num_splits: parseInt(document.getElementById('split-num').value)
  };
  
  try {
    const res = await fetch('/api/execution/split-order', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    }).then(r=>r.json());
    
    alert(`✅ Split order created: ${res.splits.length} orders`);
  } catch(e) {
    alert(`❌ Error: ${e.message}`);
  }
}

async function setupTrailingStop() {
  const data = {
    symbol: document.getElementById('trail-symbol').value,
    side: document.getElementById('trail-side').value,
    entry_price: parseFloat(document.getElementById('trail-entry').value),
    trail_percent: parseFloat(document.getElementById('trail-pct').value)
  };
  
  try {
    const res = await fetch('/api/execution/trailing-stop/setup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    }).then(r=>r.json());
    
    alert(`✅ Trailing stop setup for ${data.symbol}`);
    loadTrailingStops();
  } catch(e) {
    alert(`❌ Error: ${e.message}`);
  }
}

async function loadTrailingStops() {
  try {
    const res = await fetch('/api/execution/trailing-stops').then(r=>r.json());
    const stops = res.trailing_stops || {};
    
    if(Object.keys(stops).length === 0) {
      document.getElementById('trailing-stops-list').innerHTML = '<p style="text-align:center;color:var(--muted)">No active trailing stops</p>';
      return;
    }
    
    let html = '<table><thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Trail %</th><th>Stop Price</th><th>Actions</th></tr></thead><tbody>';
    for(const [symbol, stop] of Object.entries(stops)) {
      html += `<tr><td>${symbol}</td><td><span class="badge badge-${stop.side==='LONG'?'success':'danger'}">${stop.side}</span></td><td>${stop.entry_price}</td><td>${stop.trail_percent}%</td><td>${stop.stop_price.toFixed(2)}</td><td><button class="btn btn-danger" style="padding:4px 12px" onclick="cancelTrailing('${symbol}')">Cancel</button></td></tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('trailing-stops-list').innerHTML = html;
  } catch(e) {
    console.error('Trailing stops error:', e);
  }
}

async function cancelTrailing(symbol) {
  try {
    await fetch(`/api/execution/trailing-stop/${symbol}`, {method: 'DELETE'});
    alert(`✅ Trailing stop cancelled for ${symbol}`);
    loadTrailingStops();
  } catch(e) {
    alert(`❌ Error: ${e.message}`);
  }
}

async function loadPNL() {
  try {
    const res = await fetch('/api/pnl/summary').then(r=>r.json());
    document.getElementById('pnl-summary').innerHTML = `<pre>${JSON.stringify(res, null, 2)}</pre>`;
  } catch(e) {
    document.getElementById('pnl-summary').innerHTML = '<p style="color:var(--danger)">PNL API not available</p>';
  }
}

async function loadSignals() {
  try {
    // Load stats
    const stats = await fetch('/api/signal/stats').then(r=>r.json());
    
    // Load recent history
    const history = await fetch('/api/signal/history?limit=10').then(r=>r.json());
    
    let html = '<div class="stats-grid">';
    
    if(stats.success && stats.data) {
      const d = stats.data;
      html += `
        <div class="stat-card"><div class="stat-value">${d.total_signals || 0}</div><div class="stat-label">Total Signals</div></div>
        <div class="stat-card"><div class="stat-value" style="color:var(--success)">${d.wins || 0}</div><div class="stat-label">Wins</div></div>
        <div class="stat-card"><div class="stat-value" style="color:var(--danger)">${d.losses || 0}</div><div class="stat-label">Losses</div></div>
        <div class="stat-card"><div class="stat-value">${d.win_rate ? d.win_rate.toFixed(1) : 0}%</div><div class="stat-label">Win Rate</div></div>
        <div class="stat-card"><div class="stat-value">${d.avg_pnl_pct ? d.avg_pnl_pct.toFixed(2) : 0}%</div><div class="stat-label">Avg PNL</div></div>
        <div class="stat-card"><div class="stat-value">${d.total_pnl_usdt ? d.total_pnl_usdt.toFixed(2) : 0} USDT</div><div class="stat-label">Total PNL</div></div>
      `;
    }
    
    html += '</div>';
    
    if(history.success && history.data && history.data.length > 0) {
      html += '<table style="margin-top:20px"><thead><tr><th>Symbol</th><th>Type</th><th>Entry</th><th>Exit</th><th>PNL %</th><th>Outcome</th></tr></thead><tbody>';
      history.data.forEach(s => {
        html += `<tr>
          <td>${s.symbol}</td>
          <td><span class="badge badge-${s.signal_type==='LONG'||s.signal_type==='BUY'?'success':'danger'}">${s.signal_type}</span></td>
          <td>${s.entry_price ? s.entry_price.toFixed(2) : '-'}</td>
          <td>${s.exit_price ? s.exit_price.toFixed(2) : '-'}</td>
          <td style="color:${s.pnl_pct>=0?'var(--success)':'var(--danger)'}">${s.pnl_pct ? s.pnl_pct.toFixed(2) : '-'}%</td>
          <td><span class="badge badge-${s.outcome==='WIN'?'success':s.outcome==='LOSS'?'danger':'warning'}">${s.outcome}</span></td>
        </tr>`;
      });
      html += '</tbody></table>';
    } else {
      html += '<p style="text-align:center;color:var(--muted);margin-top:20px">No signal history yet</p>';
    }
    
    document.getElementById('signals-data').innerHTML = html;
  } catch(e) {
    console.error('Signals error:', e);
    document.getElementById('signals-data').innerHTML = '<p style="color:var(--danger)">Signals API not available</p>';
  }
}

setInterval(loadAll, 5000);
window.onload = loadAll;
</script>
</body>
</html>
"""
    return HTMLResponse(html)

# ========== NEW PAGES (v6.0) ==========

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Page de login moderne"""
    return templates.TemplateResponse("login_pro.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Page analytics avec graphiques"""
    return templates.TemplateResponse("analytics.html", {"request": request})

# Health check
@app.get("/health")
def health():
    return JSONResponse({
        "status": "healthy",
        "version": "6.0",
        "execution_engine": EXECUTION_ENABLED,
        "pnl_api": PNL_ENABLED,
        "new_features": NEW_FEATURES_ENABLED
    })
