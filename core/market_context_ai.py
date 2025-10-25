import requests, time, threading
CACHE = {"context":{}, "last_update":None}

def _loop():
    while True:
        try:
            data = requests.get("https://api.alternative.me/fng/?limit=1").json()
            score = int(data["data"][0]["value"])
            desc = data["data"][0]["value_classification"]
            CACHE["context"] = {"fear_greed":score, "sentiment":desc}
            CACHE["last_update"] = time.strftime("%H:%M:%S")
        except Exception as e:
            CACHE["error"] = str(e)
        time.sleep(3600)

def start(): threading.Thread(target=_loop, daemon=True).start()
def get(): return CACHE
