#!/usr/bin/env bash
set -euo pipefail

# ----- ENV PROPRE & EXPLICITE -----
export VIRTUAL_ENV="/opt/smartorder-pro/venv"
export PATH="/opt/smartorder-pro/venv/bin:/usr/bin:/bin"
# Ne surcharge PAS PYTHONPATH: laisse le venv faire son job
unset PYTHONPATH || true
export PYTHONUNBUFFERED=1
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Dossier de travail (code)
cd /opt/smartorder

# TRACE (1ère ligne dans les logs)
python3 - <<'PY'
import sys,os
print(f"[ENV-CHECK] exe={sys.executable} ver={sys.version.split()[0]}")
print("[ENV-CHECK] sys.path:")
print("\n".join("  - "+p for p in sys.path))
try:
    import ccxt
    print(f"[ENV-CHECK] ccxt OK: {ccxt.__version__} @ {ccxt.__file__}")
except Exception as e:
    print(f"[ENV-CHECK] ccxt IMPORT FAIL: {e}")
PY

# Lancement de l'app
exec /opt/smartorder-pro/venv/bin/python3 /opt/smartorder/ai/fusion_bridge.py
