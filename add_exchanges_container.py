#!/usr/bin/env python3
with open('/opt/smartorder-pro/web/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter le container exchanges avant POSITIONS si pas déjà présent
if '<div id="exchanges-status">' not in content:
    insert_marker = '            <!-- POSITIONS -->'
    exchanges_html = '''            <!-- EXCHANGES -->
            <div class="card">
                <h2>💱 Connected Exchanges</h2>
                <div id="exchanges-status">
                    <p style="opacity: 0.7; text-align: center;">Loading exchanges...</p>
                </div>
            </div>

            '''
    
    if insert_marker in content:
        content = content.replace(insert_marker, exchanges_html + insert_marker)
        with open('/opt/smartorder-pro/web/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✅ Container exchanges-status ajouté')
    else:
        print('⚠️  Marqueur POSITIONS non trouvé')
else:
    print('✅ Container exchanges-status déjà présent')
