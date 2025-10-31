# ========================================
# DEPLOY DIAGNOSTIC TO VPS - SmartOrder PRO
# ========================================
# Déploie et exécute le diagnostic intelligent sur le VPS
# by MAIGA ABOUBACAR

param(
    [string]$VpsHost = "smartorder",  # Alias SSH configuré
    [string]$BotPath = "/opt/smartorder-pro",
    [switch]$Watch,  # Mode continu
    [int]$Interval = 60,  # Intervalle pour mode watch
    [switch]$FixAll  # Appliquer corrections automatiques
)

Write-Host "🚀 Déploiement Diagnostic SmartOrder PRO sur VPS" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$localDiagnosticScript = "smart_diagnostic_autocorrect.py"

# Vérifier que le script existe localement
if (-not (Test-Path $localDiagnosticScript)) {
    Write-Host "❌ Script $localDiagnosticScript introuvable" -ForegroundColor Red
    exit 1
}

# 1. Copier le script sur le VPS
Write-Host "📤 Copie du script diagnostic sur VPS..." -ForegroundColor Yellow
scp $localDiagnosticScript "${VpsHost}:${BotPath}/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la copie" -ForegroundColor Red
    Write-Host "   Vérifiez la connexion SSH avec: ssh $VpsHost" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ Script copié avec succès" -ForegroundColor Green
Write-Host ""

# 2. Construire la commande à exécuter
$command = "cd $BotPath && python3 smart_diagnostic_autocorrect.py --bot-path=$BotPath"

if ($Watch) {
    $command += " --watch --interval=$Interval"
    Write-Host "🔄 Mode WATCH activé (vérification toutes les ${Interval}s)" -ForegroundColor Cyan
} elseif ($FixAll) {
    $command += " --fix-all"
    Write-Host "🔧 Mode FIX-ALL activé (corrections automatiques)" -ForegroundColor Cyan
} else {
    $command += " --fix-all"
    Write-Host "🔍 Mode ANALYSE complète activé" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "⚙️ Exécution du diagnostic sur VPS..." -ForegroundColor Yellow
Write-Host ""

# 3. Exécuter le diagnostic sur le VPS
ssh $VpsHost $command

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Diagnostic terminé avec succès" -ForegroundColor Green
    Write-Host ""
    Write-Host "📄 Rapport disponible sur VPS:" -ForegroundColor Cyan
    Write-Host "   ${BotPath}/smart_diagnostic_report.json" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📥 Pour récupérer le rapport:" -ForegroundColor Cyan
    Write-Host "   scp ${VpsHost}:${BotPath}/smart_diagnostic_report.json ." -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️ Erreur lors de l'exécution du diagnostic" -ForegroundColor Red
}
