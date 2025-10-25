#!/bin/bash
echo "🚀 Lancement SAFELOGIC Portal v5 — $(date)"
cd /opt/smartorder-pro/web/portal_v5_pro || exit 1
export PYTHONPATH=/opt/smartorder-pro
source /opt/smartorder-pro/venv/bin/activate
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8555
