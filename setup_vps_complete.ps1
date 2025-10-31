# ========================================
# SETUP VPS COMPLET - SmartOrder PRO
# ========================================
# Configuration complète en une seule commande
# by MAIGA ABOUBACAR

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIp,
    
    [string]$VpsUser = "root",
    [string]$BotPath = "/opt/smartorder-pro",
    [switch]$SkipSshSetup  # Si SSH déjà configuré
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 SETUP VPS COMPLET - SmartOrder PRO        ║" -ForegroundColor Cyan
Write-Host "║  Configuration Auto SSH + Diagnostic          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# ÉTAPE 1 : Configuration SSH Auto-Login
# ============================================
if (-not $SkipSshSetup) {
    Write-Host "┌─────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "│ ÉTAPE 1/3 : Configuration SSH Auto-Login   │" -ForegroundColor Yellow
    Write-Host "└─────────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
    
    & .\setup_ssh_auto_login.ps1 -VpsIp $VpsIp -VpsUser $VpsUser
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Erreur lors de la configuration SSH" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ SSH Auto-Login configuré avec succès !" -ForegroundColor Green
    Write-Host ""
    Start-Sleep -Seconds 2
} else {
    Write-Host "⏭️  Configuration SSH ignorée (déjà configuré)" -ForegroundColor Gray
    Write-Host ""
}

# ============================================
# ÉTAPE 2 : Déploiement du Script Diagnostic
# ============================================
Write-Host "┌─────────────────────────────────────────────┐" -ForegroundColor Yellow
Write-Host "│ ÉTAPE 2/3 : Déploiement Script Diagnostic  │" -ForegroundColor Yellow
Write-Host "└─────────────────────────────────────────────┘" -ForegroundColor Yellow
Write-Host ""

Write-Host "📤 Copie du script diagnostic sur VPS..." -ForegroundColor Cyan
scp smart_diagnostic_autocorrect.py "smartorder:${BotPath}/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la copie" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Script copié avec succès" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# ============================================
# ÉTAPE 3 : Exécution du Diagnostic Initial
# ============================================
Write-Host "┌─────────────────────────────────────────────┐" -ForegroundColor Yellow
Write-Host "│ ÉTAPE 3/3 : Diagnostic Initial du Système  │" -ForegroundColor Yellow
Write-Host "└─────────────────────────────────────────────┘" -ForegroundColor Yellow
Write-Host ""

Write-Host "🔍 Analyse complète du système..." -ForegroundColor Cyan
Write-Host ""

ssh smartorder "cd $BotPath && python3 smart_diagnostic_autocorrect.py --bot-path=$BotPath --fix-all"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️ Diagnostic terminé avec des avertissements" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "✅ Diagnostic initial terminé avec succès" -ForegroundColor Green
}

Write-Host ""

# ============================================
# ÉTAPE 4 : Récupération du Rapport
# ============================================
Write-Host "📥 Récupération du rapport diagnostic..." -ForegroundColor Cyan

$reportLocal = "diagnostic_report_$(Get-Date -Format yyyyMMdd_HHmmss).json"
scp "smartorder:${BotPath}/smart_diagnostic_report.json" $reportLocal

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Rapport sauvegardé: $reportLocal" -ForegroundColor Green
    Write-Host ""
    
    # Afficher résumé
    Write-Host "📊 RÉSUMÉ DU DIAGNOSTIC" -ForegroundColor Cyan
    Write-Host "═══════════════════════" -ForegroundColor Cyan
    
    $report = Get-Content $reportLocal | ConvertFrom-Json
    
    Write-Host "🔹 Compatibility issues: $($report.compatibility_issues.Count)" -ForegroundColor $(if ($report.compatibility_issues.Count -eq 0) { "Green" } else { "Yellow" })
    Write-Host "🔹 Incomplete code: $($report.incomplete_code.Count)" -ForegroundColor $(if ($report.incomplete_code.Count -eq 0) { "Green" } else { "Yellow" })
    Write-Host "🔹 Missing strategies: $($report.missing_strategies.missing.Count)" -ForegroundColor $(if ($report.missing_strategies.missing.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "🔹 Consistency issues: $($report.consistency_issues.Count)" -ForegroundColor $(if ($report.consistency_issues.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "🔹 Duplicate fixes: $($report.duplicate_fixes.Count)" -ForegroundColor $(if ($report.duplicate_fixes.Count -eq 0) { "Green" } else { "Yellow" })
    Write-Host "🔹 Progress gaps: $($report.progress_gaps.gaps_found.Count)" -ForegroundColor $(if ($report.progress_gaps.gaps_found.Count -eq 0) { "Green" } else { "Red" })
    
    Write-Host ""
}

# ============================================
# RÉSUMÉ FINAL
# ============================================
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  CONFIGURATION TERMINEE AVEC SUCCES !" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Votre VPS SmartOrder PRO est maintenant configure !" -ForegroundColor Cyan
Write-Host ""
Write-Host "COMMANDES UTILES:" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Connexion SSH (sans mot de passe):" -ForegroundColor Cyan
Write-Host "     ssh smartorder" -ForegroundColor White
Write-Host ""
Write-Host "  Lancer diagnostic:" -ForegroundColor Cyan
Write-Host "     .\deploy_diagnostic_to_vps.ps1 -FixAll" -ForegroundColor White
Write-Host ""
Write-Host "  Monitoring continu:" -ForegroundColor Cyan
Write-Host "     .\deploy_diagnostic_to_vps.ps1 -Watch -Interval 300" -ForegroundColor White
Write-Host ""
Write-Host "  Voir status du bot:" -ForegroundColor Cyan
Write-Host "     ssh smartorder `"systemctl status smartorder`"" -ForegroundColor White
Write-Host ""
Write-Host "  Logs en direct:" -ForegroundColor Cyan
Write-Host "     ssh smartorder `"tail -f /opt/smartorder-pro/logs/trading.log`"" -ForegroundColor White
Write-Host ""
Write-Host "  Redemarrer le bot:" -ForegroundColor Cyan
Write-Host "     ssh smartorder `"systemctl restart smartorder`"" -ForegroundColor White
Write-Host ""

Write-Host "Guide complet: .\GUIDE_SSH_DIAGNOSTIC_VPS.md" -ForegroundColor Gray
Write-Host ""
