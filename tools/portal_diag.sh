#!/bin/bash
echo "=== 🩺 SAFELOGIC Portal Diagnostic ==="
for s in smartorder-portal-v5 smartorder-websync-bridge smartorder-watchdog smartorder-guardian; do
  st=$(systemctl is-active $s)
  if [ "$st" != "active" ]; then
    echo "⚠️ $s: $st → restart"
    systemctl restart $s
  else
    echo "✅ $s: OK"
  fi
done
echo "Done."
