#!/usr/bin/env python3
"""Remove first duplicate get_active_strategies function"""

# Read
with open("/opt/smartorder-pro/api/main.py", "r") as f:
    lines = f.readlines()

# Find both functions
function_starts = []
for i, line in enumerate(lines):
    if "def get_active_strategies" in line:
        function_starts.append(i)

if len(function_starts) >= 2:
    print(f"Found {len(function_starts)} get_active_strategies functions")
    print(f"  First at line {function_starts[0]+1}")
    print(f"  Second at line {function_starts[1]+1}")
    
    # Find end of first function (before @app decorator of next function)
    first_start = function_starts[0]
    first_end = first_start
    
    for i in range(first_start + 1, len(lines)):
        if lines[i].startswith("@app.") or lines[i].startswith("# ==="):
            first_end = i
            break
    
    print(f"  First function ends at line {first_end}")
    
    # Remove lines from first_start to first_end (including decorator)
    # Find decorator before function
    decorator_line = first_start
    for i in range(first_start - 1, max(0, first_start - 5), -1):
        if '@app.get("/api/strategies")' in lines[i]:
            decorator_line = i
            break
    
    print(f"  Removing lines {decorator_line+1} to {first_end}")
    
    # Backup
    with open("/opt/smartorder-pro/api/main.py.bak_remove_dup", "w") as f:
        f.writelines(lines)
    
    # Create new content without first function
    new_lines = lines[:decorator_line] + lines[first_end:]
    
    # Write
    with open("/opt/smartorder-pro/api/main.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Removed first (duplicate) get_active_strategies function")
    print(f"   Kept second function which accepts mode parameter")
else:
    print(f"⚠️  Found only {len(function_starts)} function(s)")
