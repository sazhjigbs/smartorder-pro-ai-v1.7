#!/usr/bin/env python3
import subprocess

# Configuration correcte avec "" au lieu de ''
config = """map $http_upgrade $connection_upgrade {
  default upgrade;
  "" close;
}

server {
  listen 80;
  server_name 107.189.22.255;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name 107.189.22.255;

  ssl_certificate     /etc/nginx/ssl/safelogic/selfsigned.crt;
  ssl_certificate_key /etc/nginx/ssl/safelogic/selfsigned.key;
  ssl_protocols       TLSv1.2 TLSv1.3;
  ssl_ciphers         HIGH:!aNULL:!MD5;

  client_max_body_size 10m;

  # Dashboard SmartOrder PRO
  location /dashboard {
    root /opt/smartorder-pro/web;
    try_files /dashboard.html =404;
  }

  # API endpoints - Route vers port 8001 (stratégies + données)
  location /api/ {
    proxy_pass         http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_read_timeout 600s;
  }

  # Application principale SafeLogic (fallback)
  location / {
    proxy_pass         http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection $connection_upgrade;
    proxy_read_timeout 600s;
  }

  # Logs
  access_log /var/log/nginx/smartorder_access.log;
  error_log /var/log/nginx/smartorder_error.log;
}
"""

print("🔧 Correction finale nginx avec location /api/\n")

# Backup
subprocess.run(['cp', '/etc/nginx/sites-available/safelogic', '/etc/nginx/sites-available/safelogic.backup_final2'])
print("✅ Backup créé")

# Écrire
with open('/etc/nginx/sites-available/safelogic', 'w') as f:
    f.write(config)
print("✅ Configuration écrite")

# Tester
result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Configuration nginx valide\n")
    subprocess.run(['systemctl', 'reload', 'nginx'])
    print("✅ Nginx rechargé\n")
    
    # Test rapide
    import requests, time
    time.sleep(1)
    
    try:
        r = requests.get('https://107.189.22.255/api/strategies?mode=SPOT', verify=False, timeout=10)
        data = r.json()
        count = len(data.get('strategies', []))
        
        print(f"🧪 TEST API PUBLIC:")
        print(f"   Stratégies SPOT: {count}")
        
        if count > 0:
            print("\n🎉 SUCCÈS ! API /api/ fonctionne correctement via HTTPS")
            print("   Les stratégies sont maintenant accessibles sur le dashboard")
        else:
            print("\n⚠️  API répond mais retourne 0 stratégies")
            print("   Vérification supplémentaire nécessaire")
            
    except Exception as e:
        print(f"\n❌ Erreur test API: {e}")
else:
    print("❌ Erreur nginx:")
    print(result.stderr)
    subprocess.run(['cp', '/etc/nginx/sites-available/safelogic.backup_final2', '/etc/nginx/sites-available/safelogic'])
    print("Configuration restaurée")
