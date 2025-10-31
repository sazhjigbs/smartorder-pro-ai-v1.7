#!/usr/bin/env python3
"""
Vérification P4 - Répartition des stratégies par mode
"""
import json

# Charger config
with open('/opt/smartorder-pro/config/trading_modes.json', 'r') as f:
    data = json.load(f)

# Répartir par mode
modes = {'spot': [], 'futures': [], 'hybrid': []}
all_strategies = []

for mode_key in ['spot', 'futures', 'hybrid']:
    for strategy in data['strategies'].get(mode_key, []):
        label = strategy['label']
        enabled = strategy.get('enabled', False)
        score = strategy.get('last_score', 0)
        ai_allowed = strategy.get('ai_allowed', False)
        modes[mode_key].append(f"  - {label} (enabled: {enabled}, score: {score}, ai_allowed: {ai_allowed})")
        all_strategies.append(strategy)

# Afficher
print(f"✅ VÉRIFICATION P4 - RÉPARTITION DES 14 STRATÉGIES\n")
print(f"📊 SPOT ({len(modes['spot'])} stratégies):")
for s in modes['spot']:
    print(s)

print(f"\n📊 FUTURES ({len(modes['futures'])} stratégies):")
for s in modes['futures']:
    print(s)

print(f"\n📊 HYBRID ({len(modes['hybrid'])} stratégies):")
for s in modes['hybrid']:
    print(s)

print(f"\n🎯 TOTAL: {len(all_strategies)} stratégies")

# Vérifier AI Selector
ai_selector = data.get('ai_selector', {})
print(f"\n🤖 AI SELECTOR:")
print(f"  - Enabled: {ai_selector.get('enabled', False)}")
print(f"  - Auto Select Best: {ai_selector.get('auto_select_best', False)}")
print(f"  - Min Score: {ai_selector.get('min_score_to_trade', 0)}")

# Compter stratégies éligibles AI
eligible = [s for s in all_strategies if s.get('ai_allowed', False) and s.get('last_score', 0) >= ai_selector.get('min_score_to_trade', 70)]
print(f"  - Stratégies éligibles AI: {len(eligible)}")
if eligible:
    print(f"\n  Top 3 stratégies AI (par score):")
    for idx, s in enumerate(sorted(eligible, key=lambda x: x.get('last_score', 0), reverse=True)[:3], 1):
        print(f"    #{idx}: {s['label']} - Score: {s.get('last_score', 0)}")
