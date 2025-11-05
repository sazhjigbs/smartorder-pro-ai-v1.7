import json
with open('/tmp/strats.json') as f:
    d = json.load(f)
print('Total:', d.get('count'))
modes = {}
for s in d.get('strategies', []):
    mode = s.get('mode')
    modes[mode] = modes.get(mode, 0) + 1
print('By mode:', modes)
print('Enabled:', sum(1 for s in d.get('strategies', []) if s.get('enabled')))
