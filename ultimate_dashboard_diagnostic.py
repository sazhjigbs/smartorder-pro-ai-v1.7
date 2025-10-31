#!/usr/bin/env python3
"""
🔍 ULTIMATE DASHBOARD DIAGNOSTIC - SmartOrder PRO
=================================================
Vérifie ABSOLUMENT TOUT pour comprendre pourquoi le dashboard ne charge pas

by MAIGA ABOUBACAR
"""

import subprocess
import json
import sys
from datetime import datetime

def run_cmd(cmd):
    """Execute command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout, result.returncode
    except:
        return "", 1

def test_endpoint(url, method="GET", data=None):
    """Test API endpoint"""
    if method == "GET":
        cmd = f'curl -s -k {url}'
    else:
        cmd = f'curl -s -k -X {method} -H "Content-Type: application/json" -d \'{data}\' {url}'
    
    output, code = run_cmd(cmd)
    return output, code

print("="*80)
print("🔍 ULTIMATE DASHBOARD DIAGNOSTIC")
print("="*80)
print()

# 1. SERVICES CHECK
print("1️⃣  SERVICES STATUS")
print("-" * 40)

services = [
    "smartorder-api",
    "nginx"
]

for service in services:
    output, code = run_cmd(f"systemctl is-active {service}")
    status = output.strip()
    icon = "✅" if status == "active" else "❌"
    print(f"{icon} {service}: {status}")

print()

# 2. PORTS CHECK
print("2️⃣  PORTS LISTENING")
print("-" * 40)

ports_to_check = [8000, 8560, 8558, 80, 443]
for port in ports_to_check:
    output, code = run_cmd(f"netstat -tuln | grep :{port}")
    if output:
        print(f"✅ Port {port}: LISTENING")
    else:
        print(f"❌ Port {port}: NOT LISTENING")

print()

# 3. DASHBOARD FILE CHECK
print("3️⃣  DASHBOARD FILES")
print("-" * 40)

dashboard_path = "/opt/smartorder-pro/web/dashboard.html"
output, code = run_cmd(f"ls -lh {dashboard_path}")
if code == 0:
    print(f"✅ Dashboard file exists: {output.strip()}")
    
    # Check API_BASE in dashboard
    output, code = run_cmd(f"grep 'API_BASE' {dashboard_path} | head -1")
    print(f"📍 API_BASE config: {output.strip()}")
    
    # Check if :8000 still present
    output, code = run_cmd(f"grep ':8000' {dashboard_path}")
    if output:
        print(f"⚠️  WARNING: Port :8000 still in dashboard file!")
    else:
        print(f"✅ No hardcoded :8000 port found")
else:
    print(f"❌ Dashboard file NOT FOUND")

print()

# 4. NGINX CONFIG CHECK
print("4️⃣  NGINX CONFIGURATION")
print("-" * 40)

# Check nginx config
output, code = run_cmd("nginx -T 2>&1 | grep -A 5 'location /api'")
if "location /api/mode" in output:
    print("⚠️  /api/mode still routing separately")
else:
    print("✅ /api/mode not routing separately")

if "8560" in output or "8558" in output:
    print("⚠️  WARNING: Old ports 8560/8558 still in nginx config")
else:
    print("✅ No old ports in nginx config")

# Check what dashboard serves
output, code = run_cmd("nginx -T 2>&1 | grep -A 3 'location /dashboard'")
print(f"📍 Dashboard location:\n{output}")

print()

# 5. API ENDPOINTS TEST
print("5️⃣  API ENDPOINTS TEST")
print("-" * 40)

endpoints_to_test = [
    ("https://107.189.22.255/api/status", "GET", None),
    ("https://107.189.22.255/api/strategies", "GET", None),
    ("https://107.189.22.255/api/positions", "GET", None),
    ("https://107.189.22.255/api/funding/rates", "GET", None),
    ("https://107.189.22.255/api/exchanges", "GET", None),
]

for url, method, data in endpoints_to_test:
    endpoint_name = url.split("/")[-1] if url.split("/")[-1] else url.split("/")[-2]
    output, code = test_endpoint(url, method, data)
    
    if code == 0 and output:
        try:
            parsed = json.loads(output)
            
            # Check specific issues
            if endpoint_name == "strategies":
                if "strategies" in parsed:
                    print(f"✅ /api/strategies: OK ({len(parsed['strategies'])} strategies)")
                else:
                    print(f"⚠️  /api/strategies: Missing 'strategies' key")
                    print(f"   Response: {output[:100]}")
            
            elif endpoint_name == "exchanges":
                if "exchanges" in parsed:
                    print(f"✅ /api/exchanges: OK ({len(parsed['exchanges'])} exchanges)")
                else:
                    print(f"⚠️  /api/exchanges: Missing 'exchanges' key")
                    print(f"   Response: {output[:100]}")
            
            else:
                print(f"✅ /api/{endpoint_name}: OK")
        
        except json.JSONDecodeError:
            print(f"❌ /api/{endpoint_name}: Invalid JSON")
            print(f"   Response: {output[:100]}")
    else:
        print(f"❌ /api/{endpoint_name}: FAILED (code {code})")

print()

# 6. BROWSER CACHE HEADERS
print("6️⃣  CACHE HEADERS")
print("-" * 40)

output, code = run_cmd("curl -I -s -k https://107.189.22.255/dashboard 2>&1 | grep -i cache")
if output:
    print(f"📍 Cache headers: {output}")
else:
    print("ℹ️  No cache headers found")

print()

# 7. DASHBOARD JAVASCRIPT ERRORS
print("7️⃣  DASHBOARD JAVASCRIPT CHECK")
print("-" * 40)

# Check for console.error or fetch errors
output, code = run_cmd("grep -n 'fetch.*api' /opt/smartorder-pro/web/dashboard.html | head -5")
print(f"📍 Fetch calls in dashboard:\n{output}")

print()

# 8. API LOGS CHECK
print("8️⃣  RECENT API ERRORS")
print("-" * 40)

output, code = run_cmd("journalctl -u smartorder-api --no-pager -n 20 | grep -i error")
if output:
    print(f"⚠️  Recent errors found:\n{output}")
else:
    print("✅ No recent errors in API logs")

print()

# 9. SUMMARY
print("="*80)
print("📊 DIAGNOSTIC SUMMARY")
print("="*80)

print("\n🔧 REQUIRED ACTIONS:")
print("1. If services not active → Restart them")
print("2. If :8000 still in dashboard → Remove it")
print("3. If old ports in nginx → Update nginx config")
print("4. If API endpoints fail → Check API logs")
print("5. If cache issues → Clear nginx cache and browser cache")

print("\n✅ TO FIX IMMEDIATELY:")
output, code = run_cmd("grep ':8000' /opt/smartorder-pro/web/dashboard.html")
if output:
    print("   - Remove :8000 from dashboard.html")
    
output, code = run_cmd("systemctl is-active smartorder-api")
if output.strip() != "active":
    print("   - Start smartorder-api service")

print()
print("="*80)
print(f"Diagnostic completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
