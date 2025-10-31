#!/usr/bin/env python3
"""Fix broken script tag in dashboard.html"""

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

with open(dashboard_file, 'r') as f:
    content = f.read()

# Fix the broken script tag
content = content.replace('src=" /dashboard_persistent_fix.js>', 'src="dashboard_persistent_fix.js">')

with open(dashboard_file, 'w') as f:
    f.write(content)

print("✅ Script tag fixed")

# Verify
with open(dashboard_file, 'r') as f:
    lines = f.readlines()
    for line in lines[-5:]:
        print(line.rstrip())
