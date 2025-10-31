# Script de déploiement propre SmartOrder PRO sur VPS
Write-Host "🚀 Déploiement propre de SmartOrder PRO..." -ForegroundColor Green

$VPS_HOST = "root@107.189.22.255"
$VPS_PATH = "/opt/smartorder-pro"
$LOCAL_PATH = "C:\Users\aimet\smartorder-pro-ai-v1.7"

# Nettoyer le VPS
Write-Host "🧹 Nettoyage du VPS..." -ForegroundColor Yellow
ssh $VPS_HOST 'rm -rf /opt/smartorder-pro/* && mkdir -p /opt/smartorder-pro'

# Copier les fichiers essentiels (sans venv, logs, __pycache__)
Write-Host "📦 Copie des fichiers..." -ForegroundColor Cyan

$excludes = @(
    "venv",
    "__pycache__",
    "*.pyc",
    "logs",
    "node_modules",
    ".git",
    "*.log"
)

# Utiliser scp avec compression
scp -C -r "$LOCAL_PATH\core" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\api" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\exchanges" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\strategies" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\telegram" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\web" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\scripts" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\deployment" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\security" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\monitoring" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\config" "${VPS_HOST}:${VPS_PATH}/"
scp -C -r "$LOCAL_PATH\ai" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\*.py" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\*.txt" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\*.json" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\*.sh" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\*.md" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\Dockerfile" "${VPS_HOST}:${VPS_PATH}/"
scp -C "$LOCAL_PATH\docker-compose.yml" "${VPS_HOST}:${VPS_PATH}/"

Write-Host "📥 Installation des dépendances..." -ForegroundColor Magenta
ssh $VPS_HOST 'cd /opt/smartorder-pro && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt'

Write-Host "📁 Création des répertoires..." -ForegroundColor Blue
ssh $VPS_HOST 'cd /opt/smartorder-pro && mkdir -p logs data memory ai/memory'

Write-Host "🔐 Configuration des permissions..." -ForegroundColor Yellow
ssh $VPS_HOST 'cd /opt/smartorder-pro && chmod +x scripts/*.sh deployment/*.sh *.sh'

Write-Host "✅ Déploiement terminé !" -ForegroundColor Green
Write-Host "🎯 Pour démarrer: ssh $VPS_HOST 'cd $VPS_PATH && ./start_bot.sh'" -ForegroundColor Cyan
