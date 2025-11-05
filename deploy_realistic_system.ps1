# 🚀 DEPLOYMENT COMPLET - SmartOrder PRO AI v2.1 REALISTIC
# Déploiement du système Paper Mode réaliste avec indicateurs techniques

param(
    [switch]$SkipBackup
)

$VPS_HOST = "107.189.22.255"
$VPS_USER = "root"
$VPS_DIR = "/opt/smartorder-pro"

Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🚀 DEPLOYMENT REALISTIC SYSTEM - SmartOrder PRO AI v2.1" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 1. Test connexion
Write-Host "📡 ÉTAPE 1/7: Test de connexion VPS..." -ForegroundColor Cyan
$test = ssh root@$VPS_HOST "echo OK"
if ($test -ne "OK") {
    Write-Host "❌ Connexion VPS échouée" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Connexion VPS établie" -ForegroundColor Green
Write-Host ""

# 2. Arrêt de l'ancien système
Write-Host "🛑 ÉTAPE 2/7: Arrêt de l'ancien système..." -ForegroundColor Cyan
ssh root@$VPS_HOST "systemctl stop smartorder-paper-engine 2>/dev/null; killall -9 python3 2>/dev/null; echo 'Services arrêtés'"
Start-Sleep -Seconds 3
Write-Host "✅ Ancien système arrêté" -ForegroundColor Green
Write-Host ""

# 3. Upload du nouveau moteur réaliste
Write-Host "📤 ÉTAPE 3/7: Upload du moteur réaliste..." -ForegroundColor Cyan
Get-Content "paper_trading_engine_realistic.py" | ssh root@$VPS_HOST "cat > $VPS_DIR/paper_trading_engine_realistic.py && chmod +x $VPS_DIR/paper_trading_engine_realistic.py"
Write-Host "✅ Moteur réaliste uploadé" -ForegroundColor Green
Write-Host ""

# 4. Création des fichiers de configuration persistants
Write-Host "📋 ÉTAPE 4/7: Création des fichiers de configuration..." -ForegroundColor Cyan
Get-Content "create_persistent_configs.py" | ssh root@$VPS_HOST "cat > /tmp/create_configs.py && python3 /tmp/create_configs.py"
Write-Host ""

# 5. Installation des dépendances
Write-Host "📦 ÉTAPE 5/7: Installation des dépendances..." -ForegroundColor Cyan
ssh root@$VPS_HOST "pip3 install ccxt numpy --quiet 2>&1 | grep -E 'Successfully|already'"
Write-Host "✅ Dépendances installées" -ForegroundColor Green
Write-Host ""

# 6. Mise à jour du service systemd
Write-Host "⚙️ ÉTAPE 6/7: Configuration du service systemd..." -ForegroundColor Cyan
ssh root@$VPS_HOST @"
cat > /etc/systemd/system/smartorder-paper-realistic.service << 'EOF'
[Unit]
Description=SmartOrder PRO - Paper Trading Engine REALISTIC
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$VPS_DIR
ExecStart=/usr/bin/python3 $VPS_DIR/paper_trading_engine_realistic.py
Restart=always
RestartSec=15
StandardOutput=append:$VPS_DIR/logs/paper_realistic.log
StandardError=append:$VPS_DIR/logs/paper_realistic_error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable smartorder-paper-realistic.service
echo '✅ Service systemd configuré'
"@
Write-Host ""

# 7. Démarrage du nouveau système
Write-Host "🚀 ÉTAPE 7/7: Démarrage du système réaliste..." -ForegroundColor Cyan
ssh root@$VPS_HOST "systemctl start smartorder-paper-realistic.service"
Start-Sleep -Seconds 5

# Vérification
$status = ssh root@$VPS_HOST "systemctl is-active smartorder-paper-realistic.service"
if ($status -match "active") {
    Write-Host "✅ Système démarré avec succès" -ForegroundColor Green
} else {
    Write-Host "❌ Erreur au démarrage" -ForegroundColor Red
    ssh root@$VPS_HOST "journalctl -u smartorder-paper-realistic.service -n 20 --no-pager"
    exit 1
}
Write-Host ""

# 8. Vérification des logs
Write-Host "📊 Vérification des logs (10 dernières lignes)..." -ForegroundColor Cyan
ssh root@$VPS_HOST "tail -n 10 $VPS_DIR/logs/paper_trades_realistic.log 2>/dev/null || echo 'Logs en cours de création...'"
Write-Host ""

# 9. Attendre 60 secondes et vérifier le PnL
Write-Host "⏳ Attente de 60 secondes pour vérifier l'évolution..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

Write-Host ""
Write-Host "📈 État actuel du système:" -ForegroundColor Cyan
ssh root@$VPS_HOST "cat $VPS_DIR/config/pnl_tracker.json 2>/dev/null"
Write-Host ""

Write-Host "🎯 Derniers signaux:" -ForegroundColor Cyan
ssh root@$VPS_HOST "cat $VPS_DIR/config/last_signals.json 2>/dev/null | head -20"
Write-Host ""

# Résumé final
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ DÉPLOIEMENT TERMINÉ" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Système Paper Mode REALISTIC opérationnel" -ForegroundColor Green
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  Status  : ssh root@$VPS_HOST 'systemctl status smartorder-paper-realistic'" -ForegroundColor White
Write-Host "  Logs    : ssh root@$VPS_HOST 'tail -f $VPS_DIR/logs/paper_trades_realistic.log'" -ForegroundColor White
Write-Host "  PnL     : ssh root@$VPS_HOST 'cat $VPS_DIR/config/pnl_tracker.json'" -ForegroundColor White
Write-Host "  Signaux : ssh root@$VPS_HOST 'cat $VPS_DIR/config/last_signals.json'" -ForegroundColor White
Write-Host ""
