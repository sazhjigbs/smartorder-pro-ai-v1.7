#!/usr/bin/env python3
"""Fix /api/strategies to accept mode parameter"""

# Read
with open("/opt/smartorder-pro/api/main.py", "r") as f:
    lines = f.readlines()

# Find and fix the second get_active_strategies function (line 561)
fixed_lines = []
found_second = False
in_function = False
function_count = 0

for i, line in enumerate(lines, 1):
    if "def get_active_strategies" in line:
        function_count += 1
        if function_count == 2:  # Second occurrence
            found_second = True
            in_function = True
            # Replace function signature to accept mode parameter
            fixed_lines.append("def get_active_strategies(mode: str = None):\n")
            continue
    
    if in_function and 'mode = backend.state.get("mode"' in line:
        # Replace to use parameter first, then fallback to state
        fixed_lines.append('    mode = mode or backend.state.get("mode", "futures")\n')
        in_function = False
        continue
    
    fixed_lines.append(line)

if found_second:
    # Backup
    with open("/opt/smartorder-pro/api/main.py.bak_final", "w") as f:
        f.writelines(lines)
    
    # Write fixed version
    with open("/opt/smartorder-pro/api/main.py", "w") as f:
        f.writelines(fixed_lines)
    
    print("✅ Fixed /api/strategies to accept mode parameter")
    print("   Function signature: def get_active_strategies(mode: str = None)")
    print("   Mode resolution: mode = mode or backend.state.get('mode', 'futures')")
else:
    print("⚠️  Second get_active_strategies function not found")
