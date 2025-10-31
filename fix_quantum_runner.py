#!/usr/bin/env python3

with open('/opt/smartorder-pro/run_paper_quantum_pro.py', 'r') as f:
    lines = f.readlines()

# Find and replace quantum grid init
new_lines = []
skip_until = -1
for i, line in enumerate(lines):
    if skip_until > i:
        continue
    
    if 'self.quantum_grid = QuantumGrid(' in line:
        # Replace with proper config init
        new_lines.append('        # Stratégie Quantum Grid avec config\n')
        new_lines.append('        from strategies.quantum_grid import QuantumGridConfig\n')
        new_lines.append('        config = QuantumGridConfig(\n')
        new_lines.append("            symbol='BTCUSDT',\n")
        new_lines.append('            initial_price=100000.0,\n')
        new_lines.append('            total_investment=5000.0,\n')
        new_lines.append('            grid_levels=20,\n')
        new_lines.append('            price_range_percent=10.0\n')
        new_lines.append('        )\n')
        new_lines.append('        self.quantum_grid = QuantumGrid(config)\n')
        # Skip old init lines
        j = i + 1
        while j < len(lines) and ')' not in lines[j]:
            j += 1
        skip_until = j + 1
    else:
        new_lines.append(line)

with open('/opt/smartorder-pro/run_paper_quantum_pro.py', 'w') as f:
    f.writelines(new_lines)

print('✅ Quantum runner fixed')
