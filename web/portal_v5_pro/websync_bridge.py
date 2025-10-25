import websocket, json, ssl, certifi, datetime, time, traceback

def connect_ws():
    url = "wss://stream.bybit.com/v5/public/linear"
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    # 🔒 Contexte TLS moderne (TLS1.2-1.3 auto)
    ws.run_forever(sslopt={
        "cert_reqs": ssl.CERT_REQUIRED,
        "ca_certs": certifi.where(),
        "check_hostname": True
    })

def on_open(ws):
    print("✅ Connecté à Bybit WebSocket — souscription au flux publicTrade.BTCUSDT")
    payload = {"op": "subscribe", "args": ["publicTrade.BTCUSDT"]}
    ws.send(json.dumps(payload))

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "data" in data:
            d = data["data"][0]
            t = datetime.datetime.utcnow().strftime("%H:%M:%S")
            side = d["S"]
            price = float(d["p"])
            print(f"[{t}] {d['s']} {side} @ {price}")
    except Exception as e:
        print("Erreur message :", e)
        traceback.print_exc()

def on_error(ws, error):
    print("⚠️ Erreur WebSocket :", error)
    print("Reconnexion dans 10s…")
    time.sleep(10)
    connect_ws()

def on_close(ws, *args):
    print("❌ Connexion fermée, reconnexion dans 10s…")
    time.sleep(10)
    connect_ws()

if __name__ == "__main__":
    while True:
        try:
            connect_ws()
        except Exception as e:
            print("Bridge crashé :", e)
            time.sleep(10)
