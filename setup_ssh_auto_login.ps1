# ========================================
# SETUP SSH AUTO-LOGIN - SmartOrder PRO
# ========================================
# Configuration SSH sans mot de passe pour VPS
# by MAIGA ABOUBACAR

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIp,
    
    [Parameter(Mandatory=$true)]
    [string]$VpsUser = "root",
    
    [string]$SshKeyName = "smartorder_vps"
)

Write-Host "🔐 Configuration SSH Auto-Login pour VPS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$sshDir = "$env:USERPROFILE\.ssh"
$privateKeyPath = "$sshDir\$SshKeyName"
$publicKeyPath = "$privateKeyPath.pub"

# 1. Créer le dossier .ssh si nécessaire
if (-not (Test-Path $sshDir)) {
    Write-Host "📁 Création du dossier .ssh..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
}

# 2. Générer la clé SSH si elle n'existe pas
if (-not (Test-Path $privateKeyPath)) {
    Write-Host "🔑 Génération de la clé SSH..." -ForegroundColor Yellow
    Write-Host "   (Appuyez sur Entrée pour accepter les valeurs par défaut)" -ForegroundColor Gray
    
    ssh-keygen -t rsa -b 4096 -f $privateKeyPath -N '""' -C "smartorder-vps-$VpsUser"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erreur lors de la génération de la clé SSH" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Clé SSH générée avec succès" -ForegroundColor Green
} else {
    Write-Host "✅ Clé SSH existante trouvée" -ForegroundColor Green
}

# 3. Copier la clé publique sur le VPS
Write-Host ""
Write-Host "📤 Copie de la clé publique sur le VPS..." -ForegroundColor Yellow
Write-Host "   (Entrez votre mot de passe VPS pour la dernière fois)" -ForegroundColor Gray
Write-Host ""

# Lire la clé publique
$publicKey = Get-Content $publicKeyPath -Raw

# Copier via SSH (nécessite le mot de passe une dernière fois)
$sshCommand = @"
mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'Clé ajoutée avec succès'
"@

ssh "${VpsUser}@${VpsIp}" $sshCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Clé publique copiée avec succès sur le VPS" -ForegroundColor Green
} else {
    Write-Host "❌ Erreur lors de la copie de la clé" -ForegroundColor Red
    Write-Host "   Vous pouvez copier manuellement avec:" -ForegroundColor Yellow
    Write-Host "   type $publicKeyPath | ssh ${VpsUser}@${VpsIp} `"cat >> ~/.ssh/authorized_keys`"" -ForegroundColor Gray
    exit 1
}

# 4. Configurer le fichier SSH config pour connexion simplifiée
Write-Host ""
Write-Host "⚙️ Configuration du fichier SSH config..." -ForegroundColor Yellow

$sshConfigPath = "$sshDir\config"
$configEntry = @"

# SmartOrder PRO VPS - Auto Login
Host smartorder
    HostName $VpsIp
    User $VpsUser
    IdentityFile $privateKeyPath
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3

"@

# Ajouter au config (ou créer)
if (Test-Path $sshConfigPath) {
    # Vérifier si l'entrée existe déjà
    $existingConfig = Get-Content $sshConfigPath -Raw
    if ($existingConfig -notmatch "Host smartorder") {
        Add-Content -Path $sshConfigPath -Value $configEntry
        Write-Host "✅ Configuration SSH mise à jour" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Configuration SSH existe déjà" -ForegroundColor Yellow
    }
} else {
    Set-Content -Path $sshConfigPath -Value $configEntry
    Write-Host "✅ Fichier SSH config créé" -ForegroundColor Green
}

# 5. Tester la connexion
Write-Host ""
Write-Host "🧪 Test de connexion automatique..." -ForegroundColor Yellow
Write-Host ""

ssh -o BatchMode=yes -o ConnectTimeout=5 smartorder "echo 'Connexion automatique réussie !'"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅✅✅ SUCCÈS ! Connexion SSH automatique configurée ✅✅✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Vous pouvez maintenant vous connecter simplement avec:" -ForegroundColor Cyan
    Write-Host "   ssh smartorder" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host ""
    Write-Host "📋 Pour exécuter des commandes directement:" -ForegroundColor Cyan
    Write-Host "   ssh smartorder 'commande'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📦 Pour copier des fichiers:" -ForegroundColor Cyan
    Write-Host "   scp fichier.txt smartorder:/path/to/destination" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Test de connexion échoué" -ForegroundColor Red
    Write-Host "   Vérifiez que:" -ForegroundColor Yellow
    Write-Host "   1. Le VPS est accessible: $VpsIp" -ForegroundColor Gray
    Write-Host "   2. L'utilisateur existe: $VpsUser" -ForegroundColor Gray
    Write-Host "   3. Le service SSH est actif sur le VPS" -ForegroundColor Gray
}
