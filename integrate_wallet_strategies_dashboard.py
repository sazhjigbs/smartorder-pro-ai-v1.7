#!/usr/bin/env python3
"""
Intégration Wallets Exchange + Stratégies AI Complètes - SmartOrder PRO AI v2.0-stable
========================================================================================
Ajoute les sections manquantes dans le dashboard
"""

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'

# Lire contenu HTML à insérer
with open('dashboard_wallets_strategies.html', 'r', encoding='utf-8') as f:
    sections_html = f.read()

# Extraire les parties
import re

# Séparer HTML, CSS et JS
html_match = re.search(r'<!-- SECTION WALLETS EXCHANGE.*?</div>\s*</div>', sections_html, re.DOTALL)
style_match = re.search(r'<style>(.*?)</style>', sections_html, re.DOTALL)
script_match = re.search(r'<script>(.*?)</script>', sections_html, re.DOTALL)

html_content = html_match.group(0) if html_match else ''
style_content = style_match.group(1) if style_match else ''
script_content = script_match.group(1) if script_match else ''

# Lire dashboard actuel
with open(dashboard_file, 'r', encoding='utf-8') as f:
    dashboard = f.read()

# 1. Insérer HTML après Multi-Exchange Manager
insert_marker_html = '<!-- OPEN POSITIONS -->'
if insert_marker_html in dashboard and 'id="wallets-container"' not in dashboard:
    dashboard = dashboard.replace(insert_marker_html, html_content + '\n\n        ' + insert_marker_html)
    print('✅ Sections HTML ajoutées')
else:
    print('⚠️  Sections HTML déjà présentes ou marker non trouvé')

# 2. Ajouter CSS dans le <style> existant
if '.wallet-card' not in dashboard:
    # Trouver la fin du dernier style
    last_style_pos = dashboard.rfind('</style>')
    if last_style_pos != -1:
        dashboard = dashboard[:last_style_pos] + '\n\n' + style_content + '\n' + dashboard[last_style_pos:]
        print('✅ Styles ajoutés')

# 3. Ajouter JS à la fin du script principal
if 'updateExchangeWallets' not in dashboard:
    # Trouver dernière balise </script> avant </body>
    last_script_end = dashboard.rfind('</script>')
    if last_script_end != -1:
        dashboard = dashboard[:last_script_end] + '\n\n' + script_content + '\n' + dashboard[last_script_end:]
        print('✅ JavaScript ajouté')

# Sauvegarder
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(dashboard)

print('')
print('✅ Dashboard mis à jour avec:')
print('   - Section Wallets Exchange par exchange')
print('   - Section Stratégies AI complètes avec indicateurs')
print('   - Filtres Spot/Futures/Hybride/Activées')
print('')
print('🔄 Rechargez le dashboard: https://107.189.22.255/dashboard')
