#!/usr/bin/env python3
"""
Correction Intelligente Nginx - SmartOrder PRO
Corrige automatiquement la configuration nginx pour router /api/ vers le bon port
"""
import re
import subprocess
from datetime import datetime

print("🔧 CORRECTION INTELLIGENTE NGINX")
print("=" * 70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 1. Backup
backup_file = f'/etc/nginx/sites-available/safelogic.backup_intelligent_{int(datetime.now().timestamp())}'
subprocess.run(['cp', '/etc/nginx/sites-available/safelogic', backup_file])
print(f"✅ Backup créé: {backup_file}")

# 2. Lire la configuration
with open('/etc/nginx/sites-available/safelogic', 'r') as f:
    content = f.read()

print("\n📊 ANALYSE DE LA CONFIGURATION:")

# Détecter le port actuel pour /api/
api_match = re.search(r'location /api/.*?proxy_pass.*?:(\d+)', content, re.DOTALL)
if api_match:
    current_port = api_match.group(1)
    print(f"   Port actuel pour /api/: {current_port}")
else:
    current_port = None
    print("   ⚠️  Pas de location /api/ trouvée")

# 3. Correction intelligente
print("\n🔄 APPLICATION DES CORRECTIONS:")

if current_port and current_port != '8001':
    # Remplacer le port
    old_proxy = f'proxy_pass http://127.0.0.1:{current_port}'
    new_proxy = 'proxy_pass http://127.0.0.1:8001'
    
    content = content.replace(old_proxy, new_proxy)
    print(f"   ✅ Port {current_port} → 8001 dans location /api/")
    
elif not current_port:
    # Ajouter la location /api/ si elle n'existe pas
    # Trouver la location /dashboard pour insérer après
    dashboard_match = re.search(r'(location /dashboard.*?\n  \})', content, re.DOTALL)
    
    if dashboard_match:
        api_block = '''

  # API endpoints - Route vers port 8001 (données stratégies)
  location /api/ {
    proxy_pass         http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_read_timeout 600s;
  }
'''
        insert_pos = dashboard_match.end()
        content = content[:insert_pos] + api_block + content[insert_pos:]
        print("   ✅ Location /api/ ajoutée et routée vers port 8001")
    else:
        print("   ⚠️  Impossible de trouver où insérer location /api/")

# 4. Écrire la nouvelle configuration
with open('/etc/nginx/sites-available/safelogic', 'w') as f:
    f.write(content)

print("\n🧪 TEST DE LA CONFIGURATION:")

# 5. Tester la configuration
result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)

if result.returncode == 0:
    print("   ✅ Configuration nginx valide")
    
    # Recharger nginx
    subprocess.run(['systemctl', 'reload', 'nginx'])
    print("   ✅ Nginx rechargé avec succès")
    
    print("\n🎉 CORRECTION RÉUSSIE!")
    print(f"   📝 Backup disponible: {backup_file}")
    print("   🔗 /api/ est maintenant routé vers le port 8001")
    print("\n🧪 VÉRIFICATION:")
    
    # Test rapide
    import requests
    try:
        r = requests.get('https://107.189.22.255/api/strategies?mode=SPOT', verify=False, timeout=5)
        data = r.json()
        count = len(data.get('strategies', []))
        if count > 0:
            print(f"   ✅ API publique fonctionne: {count} stratégies SPOT")
        else:
            print("   ⚠️  API répond mais retourne 0 stratégies")
    except Exception as e:
        print(f"   ⚠️  Test API échoué: {e}")
    
else:
    print("   ❌ Erreur de configuration nginx:")
    print(result.stderr)
    print("\n   🔄 Restauration du backup...")
    subprocess.run(['cp', backup_file, '/etc/nginx/sites-available/safelogic'])
    print("   ✅ Configuration restaurée")

print("\n" + "=" * 70)
