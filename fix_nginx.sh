#!/bin/bash
# Fix Nginx - Router /api/ vers port 8001
echo "🔧 Correction automatique de la configuration Nginx..."

# Backup
cp /etc/nginx/sites-available/safelogic /etc/nginx/sites-available/safelogic.backup_auto_$(date +%s)

# Lire la config actuelle
nginx_config=$(cat /etc/nginx/sites-available/safelogic)

# Insérer la route /api/ AVANT location /
python3 << 'EOFPYTHON'
with open('/etc/nginx/sites-available/safelogic', 'r') as f:
    lines = f.readlines()

# Trouver où insérer la nouvelle location
new_lines = []
api_route_added = False

for i, line in enumerate(lines):
    # Si on trouve "location /" et qu'on n'a pas encore ajouté /api/
    if 'location /' in line and not api_route_added and 'location /dashboard' not in line:
        # Ajouter la route /api/ juste avant
        new_lines.append('\n')
        new_lines.append('  # API endpoints - Router vers port 8001 (stratégies)\n')
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
        api_route_added = True
    
    new_lines.append(line)

# Écrire la nouvelle config
with open('/etc/nginx/sites-available/safelogic', 'w') as f:
    f.writelines(new_lines)

print("✅ Configuration Nginx mise à jour")
EOFPYTHON

# Tester et recharger nginx
echo "🧪 Test de la configuration..."
if nginx -t 2>&1; then
    echo "✅ Configuration valide"
    systemctl reload nginx
    echo "✅ Nginx rechargé"
    
    # Vérifier que ça marche
    echo ""
    echo "🔍 Test de la correction..."
    sleep 2
    
    result=$(curl -k -s https://localhost/api/strategies?mode=SPOT | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('strategies', [])))")
    
    if [ "$result" -gt "0" ]; then
        echo "✅ SUCCÈS! $result stratégies maintenant disponibles via HTTPS"
        echo ""
        echo "🎉 Dashboard https://107.189.22.255/dashboard devrait maintenant afficher les stratégies!"
    else
        echo "⚠️  Toujours 0 stratégies, vérification supplémentaire nécessaire"
    fi
else
    echo "❌ Erreur de configuration, restauration du backup..."
    cp /etc/nginx/sites-available/safelogic.backup_auto_* /etc/nginx/sites-available/safelogic
fi
