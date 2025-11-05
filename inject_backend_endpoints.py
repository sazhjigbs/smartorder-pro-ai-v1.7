#!/usr/bin/env python3
"""
INJECTION AUTOMATIQUE DES ENDPOINTS BACKEND CRITIQUES
Script pour ajouter tous les nouveaux endpoints dans main.py
"""

with open('/opt/smartorder-pro/api/main.py', 'r') as f:
    content = f.read()

# Lire le fichier d'endpoints
with open('/tmp/backend_endpoints_critical.py', 'r') as f:
    endpoints_code = f.read()

# Extraire seulement le code des fonctions (sans imports redondants)
endpoints_only = '\n'.join([
    line for line in endpoints_code.split('\n')
    if not line.startswith('import ') and not line.startswith('from ')
])

# Trouver où insérer (avant if __name__)
if "if __name__ == '__main__':" in content:
    # Ajouter avant le bloc main
    content = content.replace(
        "if __name__ == '__main__':",
        endpoints_only + "\n\nif __name__ == '__main__':"
    )
else:
    # Ajouter à la fin
    content += "\n\n" + endpoints_only

# Sauvegarder
with open('/opt/smartorder-pro/api/main.py', 'w') as f:
    f.write(content)

print('✅ Endpoints backend injectés dans main.py')
print('   Total: 7 nouveaux endpoints ajoutés')
