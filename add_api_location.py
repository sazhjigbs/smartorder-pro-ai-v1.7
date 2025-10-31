#!/usr/bin/env python3
"""
Ajout de location /api/ dans nginx - CORRECTIF
"""
import subprocess

print("🔧 Ajout location /api/ dans nginx\n")

# Backup
subprocess.run(['cp', '/etc/nginx/sites-available/safelogic', '/etc/nginx/sites-available/safelogic.backup_before_api'])
print("✅ Backup créé\n")

# Lire
with open('/etc/nginx/sites-available/safelogic', 'r') as f:
    lines = f.readlines()

# Trouver où insérer (après location /dashboard)
new_lines = []
api_added = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Après la fermeture de location /dashboard, ajouter location /api/
    if 'location /dashboard' in line and not api_added:
        # Trouver la fermeture de ce bloc
        brace_count = 0
        j = i
        while j < len(lines):
            if '{' in lines[j]:
                brace_count += 1
            if '}' in lines[j]:
                brace_count -= 1
                if brace_count == 0:
                    # C'est la fin du bloc dashboard
                    # On doit ajouter APRÈS cette ligne
                    break
            j += 1
        
        # Continuer à copier jusqu'à la fin du bloc dashboard
        while i < j:
            i += 1
            if i < len(lines):
                new_lines.append(lines[i])
        
        # Ajouter location /api/ après
        new_lines.append('\n')
        new_lines.append('  # API endpoints - Route vers port 8001 (stratégies + données)\n')
        new_lines.append('  location /api/ {\n')
        new_lines.append('    proxy_pass         http://127.0.0.1:8001;\n')
        new_lines.append('    proxy_http_version 1.1;\n')
        new_lines.append('    proxy_set_header   Host $host;\n')
        new_lines.append('    proxy_set_header   X-Real-IP $remote_addr;\n')
        new_lines.append('    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;\n')
        new_lines.append('    proxy_set_header   X-Forwarded-Proto $scheme;\n')
        new_lines.append('    proxy_read_timeout 600s;\n')
        new_lines.append('  }\n')
        
        api_added = True
        print("✅ Bloc location /api/ ajouté après /dashboard")

# Si pas trouvé dashboard, chercher location /
if not api_added:
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Avant location /, ajouter /api/
        if 'location / {' in line and not api_added:
            # Insérer AVANT cette ligne
            new_lines.pop()  # Retirer location /
            
            new_lines.append('\n')
            new_lines.append('  # API endpoints - Route vers port 8001\n')
            new_lines.append('  location /api/ {\n')
            new_lines.append('    proxy_pass         http://127.0.0.1:8001;\n')
            new_lines.append('    proxy_http_version 1.1;\n')
            new_lines.append('    proxy_set_header   Host $host;\n')
            new_lines.append('    proxy_set_header   X-Real-IP $remote_addr;\n')
            new_lines.append('    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;\n')
            new_lines.append('    proxy_set_header   X-Forwarded-Proto $scheme;\n')
            new_lines.append('    proxy_read_timeout 600s;\n')
            new_lines.append('  }\n')
            new_lines.append('\n')
            new_lines.append(line)  # Remettre location /
            
            api_added = True
            print("✅ Bloc location /api/ ajouté avant location /")

# Écrire
with open('/etc/nginx/sites-available/safelogic', 'w') as f:
    f.writelines(new_lines)

# Tester
result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)

if result.returncode == 0:
    print("\n✅ Configuration nginx valide")
    subprocess.run(['systemctl', 'reload', 'nginx'])
    print("✅ Nginx rechargé\n")
    
    # Test
    import requests
    try:
        r = requests.get('https://107.189.22.255/api/strategies?mode=SPOT', verify=False, timeout=5)
        data = r.json()
        count = len(data.get('strategies', []))
        print(f"🧪 Test: {count} stratégies SPOT retournées")
        
        if count > 0:
            print("✅ SUCCÈS - API fonctionne correctement !")
        else:
            print("⚠️  API répond mais retourne 0 stratégies")
    except Exception as e:
        print(f"❌ Test échoué: {e}")
else:
    print("\n❌ Erreur nginx:")
    print(result.stderr)
    subprocess.run(['cp', '/etc/nginx/sites-available/safelogic.backup_before_api', '/etc/nginx/sites-available/safelogic'])
    print("✅ Configuration restaurée")
