#!/usr/bin/env python3
"""
Intègre dashboard_persistent_fix.js DIRECTEMENT dans dashboard.html
pour éviter le problème de nginx qui ne sert pas les fichiers .js
"""

import re

dashboard_file = '/opt/smartorder-pro/web/dashboard.html'
fix_js_file = '/opt/smartorder-pro/web/dashboard_persistent_fix.js'

# Lire le contenu du script JS
with open(fix_js_file, 'r', encoding='utf-8') as f:
    fix_js_content = f.read()

# Lire le dashboard HTML
with open(dashboard_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Supprimer l'ancienne référence externe
html_content = re.sub(
    r'<script src="dashboard_persistent_fix\.js"></script>',
    '',
    html_content
)

# Injecter le code JS INLINE juste avant </body>
inline_script = f'''
    <script>
    // ===== PERSISTENCE FIX INLINE v3.0 =====
{fix_js_content}
    </script>
</body>'''

html_content = html_content.replace('</body>', inline_script)

# Sauvegarder
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Script de persistance intégré INLINE dans dashboard.html")
print(f"   Total lignes JS: {fix_js_content.count(chr(10))}")
print("   Le script se chargera maintenant sans dépendre de nginx")
