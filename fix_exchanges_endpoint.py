#!/usr/bin/env python3
"""Fix /api/exchanges endpoint crash"""

import re

# Read
with open("/opt/smartorder-pro/api/main.py", "r") as f:
    content = f.read()

# Find and replace the get_exchanges function
pattern = r'(def get_exchanges\(\):.*?)(connected = ex in backend\.state\["active_exchanges"\])'
replacement = r'\1connected = ex in backend.state.get("active_exchanges", backend.exchanges)'

content_new = re.sub(pattern, replacement, content, flags=re.DOTALL)

if content_new != content:
    # Backup
    with open("/opt/smartorder-pro/api/main.py.bak_exchanges", "w") as f:
        f.write(content)
    
    # Write
    with open("/opt/smartorder-pro/api/main.py", "w") as f:
        f.write(content_new)
    
    print("✅ Fixed /api/exchanges endpoint")
    print("   Old: backend.state['active_exchanges']")
    print("   New: backend.state.get('active_exchanges', backend.exchanges)")
else:
    print("⚠️  Pattern not found or already fixed")
