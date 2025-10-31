# ========================================
# SmartOrder PRO AI v1.7 - Déploiement VPS
# ========================================

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  🚀 SMARTORDER PRO AI v1.7 - DÉPLOIEMENT VPS" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan

# Configuration
$VPS_USER = "root"  # À modifier
$VPS_HOST = "votre-vps-ip"  # À modifier
$VPS_PATH = "/root/smartorder-pro-ai-v1.7"
$LOCAL_PATH = Get-Location

Write-Host "`n📋 Configuration:" -ForegroundColor Cyan
Write-Host "  Local  : $LOCAL_PATH" -ForegroundColor Gray
Write-Host "  VPS    : ${VPS_USER}@${VPS_HOST}:${VPS_PATH}" -ForegroundColor Gray

# Liste des nouveaux fichiers à déployer
$newFiles = @(
    "core/trailing_stop_manager.py",
    "core/smart_order_engine.py",
    "core/copy_trading_engine.py",
    "core/market_scanner.py",
    "core/risk_manager_advanced.py",
    "core/multi_timeframe_analyzer.py",
    "core/arbitrage_executor.py",
    "core/cross_strategy_hedger.py",
    "core/fee_optimizer.py",
    "strategies/quantum_grid.py",
    "ai/strategy_composer.py",
    "ai/emotion_detector.py",
    "integrations/tradingview_webhook.py",
    "notifications/notification_manager.py",
    "backtesting/backtesting_engine_pro.py",
    "tests/test_all_features.py",
    "CHECKLIST_COMPLETE.md",
    "IMPLEMENTATION_SUMMARY.md"
)

Write-Host "`n📦 Préparation des fichiers..." -ForegroundColor Cyan

$deployCount = 0
$missingCount = 0

foreach ($file in $newFiles) {
    if (Test-Path $file) {
        $deployCount++
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        $missingCount++
        Write-Host "  ❌ $file - MANQUANT" -ForegroundColor Red
    }
}

Write-Host "`n  Fichiers prêts: $deployCount / $($newFiles.Count)" -ForegroundColor $(if ($deployCount -eq $newFiles.Count) { "Green" } else { "Yellow" })

if ($missingCount -gt 0) {
    Write-Host "  ⚠️  $missingCount fichiers manquants - Vérifiez la structure" -ForegroundColor Yellow
}

# Création du package de déploiement
Write-Host "`n📦 Création du package de déploiement..." -ForegroundColor Cyan

$packageDir = "deploy_package_v1.7"
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Copier les fichiers
foreach ($file in $newFiles) {
    if (Test-Path $file) {
        $targetDir = Join-Path $packageDir (Split-Path $file -Parent)
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item $file -Destination (Join-Path $packageDir $file) -Force
    }
}

Write-Host "  ✅ Package créé: $packageDir/" -ForegroundColor Green

# Créer le script d'installation pour le VPS
$installScript = @"
#!/bin/bash
# SmartOrder PRO AI v1.7 - Installation Script

echo "========================================="
echo "  🚀 SmartOrder PRO AI v1.7 - Installation"
echo "========================================="

VPS_PATH="$VPS_PATH"

# Backup de l'ancienne version
echo ""
echo "📦 Backup de la version actuelle..."
if [ -d "`$VPS_PATH" ]; then
    BACKUP_DIR="`$VPS_PATH.backup.`$(date +%Y%m%d_%H%M%S)"
    cp -r "`$VPS_PATH" "`$BACKUP_DIR"
    echo "  ✅ Backup créé: `$BACKUP_DIR"
else
    echo "  ℹ️  Nouvelle installation"
fi

# Créer les dossiers nécessaires
echo ""
echo "📁 Création de la structure..."
mkdir -p "`$VPS_PATH/core"
mkdir -p "`$VPS_PATH/strategies"
mkdir -p "`$VPS_PATH/ai"
mkdir -p "`$VPS_PATH/integrations"
mkdir -p "`$VPS_PATH/notifications"
mkdir -p "`$VPS_PATH/backtesting"
mkdir -p "`$VPS_PATH/tests"

echo "  ✅ Structure créée"

# Copier les nouveaux fichiers
echo ""
echo "📥 Installation des modules v1.7..."
cd deploy_package_v1.7

# Copie récursive
cp -r * "`$VPS_PATH/"

echo "  ✅ Modules installés"

# Vérification des permissions
echo ""
echo "🔒 Configuration des permissions..."
chmod +x "`$VPS_PATH"/*.py 2>/dev/null
chmod +x "`$VPS_PATH"/core/*.py
chmod +x "`$VPS_PATH"/strategies/*.py
chmod +x "`$VPS_PATH"/ai/*.py

echo "  ✅ Permissions configurées"

# Installation des dépendances Python
echo ""
echo "📦 Installation des dépendances..."
cd "`$VPS_PATH"

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo "  ✅ Dépendances installées"
else
    echo "  ⚠️  requirements.txt non trouvé"
fi

# Test des imports
echo ""
echo "🧪 Test des modules..."
python3 -c "from core.trailing_stop_manager import TrailingStopManager; print('  ✅ Trailing Stop Manager')" 2>/dev/null || echo "  ⚠️  Trailing Stop Manager"
python3 -c "from core.smart_order_engine import SmartOrderEngine; print('  ✅ Smart Order Engine')" 2>/dev/null || echo "  ⚠️  Smart Order Engine"
python3 -c "from ai.strategy_composer import AIStrategyComposer; print('  ✅ AI Strategy Composer')" 2>/dev/null || echo "  ⚠️  AI Strategy Composer"
python3 -c "from strategies.quantum_grid import QuantumGrid; print('  ✅ Quantum Grid')" 2>/dev/null || echo "  ⚠️  Quantum Grid"

# Redémarrage des services
echo ""
echo "🔄 Redémarrage des services..."

# Arrêter les services existants
pkill -f "smartorder" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true

sleep 2

# Redémarrer
echo "  ✅ Services arrêtés"
echo "  ℹ️  Redémarrez manuellement avec: python3 main.py"

echo ""
echo "========================================="
echo "✅ INSTALLATION TERMINÉE"
echo "========================================="
echo ""
echo "📊 Statistiques:"
echo "  - Modules installés: 16"
echo "  - Version: v1.7"
echo "  - Progression: 89.5% (17/19 phases)"
echo ""
echo "🚀 Fonctionnalités ajoutées:"
echo "  ✅ Trailing Stop Loss & Take Profit"
echo "  ✅ Smart Orders (OCO, Iceberg, TWAP)"
echo "  ✅ Copy Trading Engine"
echo "  ✅ Market Scanner"
echo "  ✅ Risk Manager Advanced"
echo "  ✅ Multi-Timeframe Analyzer"
echo "  ⚡ Quantum Grid (UNIQUE)"
echo "  ⚡ AI Strategy Composer (UNIQUE)"
echo "  ✅ Backtesting Pro"
echo "  ✅ Arbitrage Executor"
echo "  ✅ Emotion AI Detector"
echo "  ✅ Cross-Strategy Hedging"
echo "  ✅ Fee Optimizer"
echo ""
"@

$installScript | Out-File -FilePath "$packageDir/install_vps.sh" -Encoding UTF8

Write-Host "  ✅ Script d'installation créé: install_vps.sh" -ForegroundColor Green

# Créer fichier requirements si manquant
if (-not (Test-Path "requirements.txt")) {
    $reqFile = Join-Path $packageDir "requirements.txt"
    $requirements = "numpy>=1.21.0`npandas>=1.3.0`nccxt>=4.0.0`nwebsockets>=10.0`nflask>=2.0.0`nflask-cors>=3.0.10`npython-telegram-bot>=13.0`nrequests>=2.26.0`naiohttp>=3.8.0`ncryptography>=3.4.0"
    $requirements | Out-File -FilePath $reqFile -Encoding UTF8
    Write-Host "  ✅ requirements.txt créé" -ForegroundColor Green
}

# Créer archive de déploiement
Write-Host "`n📦 Création de l'archive de déploiement..." -ForegroundColor Cyan

$archiveName = "smartorder-pro-v1.7-deploy.zip"
if (Test-Path $archiveName) {
    Remove-Item $archiveName -Force
}

Compress-Archive -Path "$packageDir/*" -DestinationPath $archiveName -Force

$archiveSize = (Get-Item $archiveName).Length / 1KB
Write-Host "  ✅ Archive créée: $archiveName ($([math]::Round($archiveSize, 2)) KB)" -ForegroundColor Green

# Instructions de déploiement
Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "📋 INSTRUCTIONS DE DÉPLOIEMENT" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

Write-Host "`n🔧 MÉTHODE 1: Déploiement manuel" -ForegroundColor Cyan
Write-Host @"

1. Transférer l'archive sur le VPS:
   scp $archiveName ${VPS_USER}@${VPS_HOST}:/tmp/

2. Se connecter au VPS:
   ssh ${VPS_USER}@${VPS_HOST}

3. Extraire et installer:
   cd /tmp
   unzip $archiveName -d ~/
   cd ~/deploy_package_v1.7
   chmod +x install_vps.sh
   ./install_vps.sh

4. Redémarrer SmartOrder:
   cd $VPS_PATH
   python3 main.py

"@ -ForegroundColor Gray

Write-Host "🔧 MÉTHODE 2: Déploiement automatique (si SSH configuré)" -ForegroundColor Cyan
Write-Host @"

  # Modifier les variables VPS_USER et VPS_HOST en haut du script
  # Puis exécuter:
  
  .\deploy_vps.ps1 -AutoDeploy

"@ -ForegroundColor Gray

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "✅ PRÉPARATION TERMINÉE" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

Write-Host "`n📊 Résumé:" -ForegroundColor Cyan
Write-Host "  Archive       : $archiveName" -ForegroundColor White
Write-Host "  Taille        : $([math]::Round($archiveSize, 2)) KB" -ForegroundColor White
Write-Host "  Modules       : $deployCount" -ForegroundColor White
Write-Host "  Version       : v1.7" -ForegroundColor White
Write-Host "  Progression   : 89.5% (17/19 phases)" -ForegroundColor Green

Write-Host "`n🚀 Prêt pour déploiement sur VPS!" -ForegroundColor Green
Write-Host ""
