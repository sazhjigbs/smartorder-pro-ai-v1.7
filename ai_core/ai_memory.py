import json, os, time, threading
from typing import Any, Dict

class AIMemory:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.isfile(self.path):
            self._write({"created_at": time.time(), "last_update": None, "metrics": {}, "notes": []})

    def _read(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception:
                return {"created_at": time.time(), "last_update": None, "metrics": {}, "notes": []}

    def _write(self, data: Dict[str, Any]) -> None:
        with self._lock:
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)

    def get(self) -> Dict[str, Any]:
        return self._read()

    def update_metric(self, key: str, value: Any) -> None:
        data = self._read()
        data.setdefault("metrics", {})[key] = value
        data["last_update"] = time.time()
        self._write(data)

    def append_note(self, note: str) -> None:
        data = self._read()
        data.setdefault("notes", []).append({"t": time.time(), "msg": note})
        data["last_update"] = time.time()
        self._write(data)
