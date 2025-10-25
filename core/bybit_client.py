import os, time, hmac, hashlib, json, logging
import requests
from typing import Dict, Any, Tuple

LOG = logging.getLogger("bybit_client")
LOG.setLevel(logging.INFO)
fh = logging.FileHandler("/opt/smartorder-pro/logs/bybit_client.log")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
LOG.addHandler(fh)

API_KEY = os.getenv("BYBIT_API_KEY", "")
API_SECRET = os.getenv("BYBIT_API_SECRET", "")
RECV_WINDOW = os.getenv("BYBIT_RECV_WINDOW", "5000")
BASE = "https://api.bybit.com"  # v5 unified

def _ts_ms() -> str:
    # Toujours en millisecondes, string
    return str(int(time.time() * 1000))

def _sign(payload: str) -> str:
    # signature hex hmac_sha256(secret, payload)
    return hmac.new(API_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()

def _headers(query_or_body: str) -> Dict[str, str]:
    """
    Signature v5: sign = HMAC_SHA256( timestamp + api_key + recv_window + query_or_body )
    query_or_body = string de la query (GET) ou body JSON (POST) tel qu’envoyé.
    """
    if not API_KEY or not API_SECRET:
        raise RuntimeError("BYBIT_API_KEY / BYBIT_API_SECRET absents")
    ts = _ts_ms()
    sign_str = f"{ts}{API_KEY}{RECV_WINDOW}{query_or_body}"
    sign = _sign(sign_str)
    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
        "X-BAPI-SIGN": sign,
        "Content-Type": "application/json",
    }

def _get(path: str, params: Dict[str, Any]) -> Tuple[bool, Any]:
    # Encoder la query triée
    items = []
    for k in sorted(params.keys()):
        v = params[k]
        items.append(f"{k}={v}")
    qs = "&".join(items)
    url = f"{BASE}{path}?{qs}" if qs else f"{BASE}{path}"
    try:
        r = requests.get(url, headers=_headers(qs), timeout=10)
        data = r.json()
        ok = (data.get("retCode") == 0)
        if not ok:
            LOG.error("GET %s -> %s", path, data)
        return ok, data
    except Exception as e:
        LOG.exception("GET %s failed: %s", path, e)
        return False, {"error": str(e)}

def _post(path: str, body: Dict[str, Any]) -> Tuple[bool, Any]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    url = f"{BASE}{path}"
    try:
        r = requests.post(url, data=raw, headers=_headers(raw), timeout=10)
        data = r.json()
        ok = (data.get("retCode") == 0)
        if not ok:
            LOG.error("POST %s -> %s", path, data)
        return ok, data
    except Exception as e:
        LOG.exception("POST %s failed: %s", path, e)
        return False, {"error": str(e)}

# --------- Publics du portail ---------

def system_ping() -> Dict[str, Any]:
    ok, data = _get("/v5/market/time", {})
    return {"ok": ok, "data": data}

def wallet_spot_balances() -> Dict[str, Any]:
    # Unified wallet – assets (spot y sont visibles)
    ok, data = _get("/v5/asset/transfer/query-asset-info", {"accountType": "UNIFIED"})
    if not ok:
        return {"spot": [{"error": data}]}
    # Normaliser un peu
    result = []
    for a in data.get("result", {}).get("list", []):
        coin = a.get("coin", "-")
        free = a.get("free", a.get("walletBalance", "0"))
        result.append({"asset": coin, "free": free})
    return {"spot": result}

def futures_positions() -> Dict[str, Any]:
    # Positions perp futures (UNIFIED)
    ok, data = _get("/v5/position/list", {"category": "linear"})
    if not ok:
        return {"futures": [{"error": data}]}
    out = []
    for p in data.get("result", {}).get("list", []):
        out.append({
            "symbol": p.get("symbol"),
            "side": p.get("side"),
            "size": p.get("size"),
            "entryPrice": p.get("avgPrice"),
            "unrealPnl": p.get("unrealisedPnl"),
            "leverage": p.get("leverage"),
        })
    return {"futures": out}
