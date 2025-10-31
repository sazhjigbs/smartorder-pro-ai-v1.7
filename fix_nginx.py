#!/usr/bin/env python3
import re

# Backup
import shutil
shutil.copy('/etc/nginx/sites-available/safelogic', '/etc/nginx/sites-available/safelogic.backup_auto')

# Read
with open('/etc/nginx/sites-available/safelogic', 'r') as f:
    lines = f.readlines()

# Process
new_lines = []
in_api_mode = False
in_api_sentiment = False

for line in lines:
    if 'location /api/mode {' in line:
        in_api_mode = True
        new_lines.append('  # ' + line)
    elif 'location /api/sentiment {' in line:
        in_api_sentiment = False
        new_lines.append('  # ' + line)
    elif (in_api_mode or in_api_sentiment) and line.strip() == '}':
        new_lines.append('  # ' + line)
        in_api_mode = False
        in_api_sentiment = False
    elif in_api_mode or in_api_sentiment:
        new_lines.append('  # ' + line)
    else:
        new_lines.append(line)

# Write
with open('/etc/nginx/sites-available/safelogic', 'w') as f:
    f.writelines(new_lines)

print('✅ Nginx config updated - api/mode and api/sentiment commented out')
