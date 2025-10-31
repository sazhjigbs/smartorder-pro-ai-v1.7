#!/usr/bin/env python3
"""Analyse complète de rentabilité du bot"""

import json

# Charger données
with open('/opt/smartorder-pro/config/pnl_tracker.json') as f:
    pnl_data = json.load(f)

with open('/opt/smartorder-pro/config/positions.json') as f:
    positions = json.load(f)

# Stats globales
total_pnl = pnl_data.get('total_pnl', 0)
trades = pnl_data.get('trades', [])
by_strategy = pnl_data.get('by_strategy', {})

open_pos = [p for p in positions if p.get('status') == 'open']
closed_pos = [p for p in positions if p.get('status') == 'closed']

# Analyse trades
winning = [t for t in trades if t['pnl'] > 0]
losing = [t for t in trades if t['pnl'] < 0]
total_trades = len(trades)

win_rate = (len(winning) / total_trades * 100) if total_trades > 0 else 0
total_profit = sum(t['pnl'] for t in winning)
total_loss = sum(t['pnl'] for t in losing)
profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0

print("=" * 70)
print("ANALYSE DE RENTABILITE - SmartOrder PRO AI")
print("=" * 70)
print()

print("PNL GLOBAL")
print("-" * 70)
print(f"Total PnL:        ${total_pnl:.2f}")
if total_pnl > 0:
    print(f"Rentabilite:      PROFITABLE (+{total_pnl:.2f})")
elif total_pnl < 0:
    print(f"Rentabilite:      EN PERTE ({total_pnl:.2f})")
else:
    print(f"Rentabilite:      EQUILIBRE")
print()

print("STATISTIQUES DES TRADES")
print("-" * 70)
print(f"Total trades:     {total_trades}")
print(f"Trades gagnants:  {len(winning)} ({win_rate:.1f}%)")
print(f"Trades perdants:  {len(losing)} ({100-win_rate:.1f}%)")
print(f"Win Rate:         {win_rate:.1f}%")
print(f"Profit Factor:    {profit_factor:.2f}")
print()

print("GAINS ET PERTES")
print("-" * 70)
print(f"Total gains:      +${total_profit:.2f}")
print(f"Total pertes:     ${total_loss:.2f}")
print(f"Net:              ${total_pnl:.2f}")
print()

print("PERFORMANCE PAR STRATEGIE")
print("-" * 70)
for strategy, pnl in sorted(by_strategy.items(), key=lambda x: x[1], reverse=True):
    status = "[+]" if pnl > 0 else "[-]" if pnl < 0 else "[=]"
    print(f"{status} {strategy:30s} ${pnl:+9.2f}")
print()

print("POSITIONS")
print("-" * 70)
print(f"Positions ouvertes:  {len(open_pos)}")
print(f"Positions fermees:   {len(closed_pos)}")

if open_pos:
    print()
    print("Positions en cours:")
    for p in open_pos[:10]:
        pnl_val = p.get('pnl', 0)
        pnl_sign = "[+]" if pnl_val >= 0 else "[-]"
        print(f"  {pnl_sign} {p['symbol']:12s} {p['side']:4s} "
              f"{p['amount']:.6f} @ ${p['entry_price']:.2f} | PnL: ${pnl_val:.2f}")
print()

if trades:
    best = max(trades, key=lambda t: t['pnl'])
    worst = min(trades, key=lambda t: t['pnl'])
    
    print("MEILLEUR TRADE")
    print("-" * 70)
    print(f"  {best['symbol']} {best['side']} {best['amount']:.6f}")
    print(f"  Entry: ${best['entry']:.2f} -> Exit: ${best['exit']:.2f}")
    print(f"  PnL: +${best['pnl']:.2f} ({best['strategy']})")
    print()
    
    print("PIRE TRADE")
    print("-" * 70)
    print(f"  {worst['symbol']} {worst['side']} {worst['amount']:.6f}")
    print(f"  Entry: ${worst['entry']:.2f} -> Exit: ${worst['exit']:.2f}")
    print(f"  PnL: ${worst['pnl']:.2f} ({worst['strategy']})")
    print()

print("=" * 70)
print("CONCLUSION")
print("=" * 70)

if total_pnl > 0:
    print("RESULTAT: Le bot est RENTABLE")
    print(f"Profit net: +${total_pnl:.2f}")
elif total_pnl == 0:
    print("RESULTAT: Le bot est a l'EQUILIBRE")
else:
    print("RESULTAT: Le bot est EN PERTE")
    print(f"Perte nette: ${total_pnl:.2f}")
    print()
    print("Raisons possibles:")
    print("  - Mode simulation avec prix aleatoires (+/- 0.5%)")
    print("  - Pas de vraie strategie technique (trades aleatoires)")
    print("  - Frais de trading non comptabilises")
    print("  - Besoin d'optimisation des parametres")
    print("  - Win rate trop faible ou mauvais ratio risque/rendement")

print("=" * 70)
