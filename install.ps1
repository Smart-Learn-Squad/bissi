#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Bienvenue dans l'installateur de Bissi" -ForegroundColor Cyan
Write-Host "Voici ce qui va se passer :"
Write-Host "  1. Verification et installation des outils requis"
Write-Host "  2. Clonage du repo GitHub"
Write-Host "  3. Creation du virtualenv Python"
Write-Host "  4. Installation de huggingface-cli"
Write-Host "  5. Installation des dependances npm"
Write-Host "  6. Telechargement du modele IA (~3 GB)"
Write-Host "  7. Ouverture de VS Code"
Write-Host "  8. Lancement de l'application"
Write-Host ""

# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

function Reload-Path {
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

function Install-IfMissing {
    param(
        [string]$Tool,
        [string]$WingetId,
        [string]$Url
    )
    if (Get-Command $Tool -ErrorAction SilentlyContinue) {
        Write-Host "  OK $Tool deja installe" -ForegroundColor Green
        return
    }

    if (-not (Get-Command "winget" -ErrorAction SilentlyContinue)) {
        Write-Host "  X winget non disponible." -ForegroundColor Red
        Write-Host "    Installe $Tool manuellement : $Url"
        exit 1
    }

    Write-Host "  -> Installation de $Tool via winget..." -ForegroundColor Yellow
    winget install --id $WingetId -e --silent `
        --accept-source-agreements `
        --accept-package-agreements

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  X Echec de l'installation de $Tool" -ForegroundColor Red
        Write-Host "    Installe-le manuellement : $Url"
        exit 1
    }

    Reload-Path

    if (-not (Get-Command $Tool -ErrorAction SilentlyContinue)) {
        Write-Host "  X $Tool installe mais introuvable dans le PATH." -ForegroundColor Red
        Write-Host "    Ferme et rouvre ce terminal, puis relance le script."
        exit 1
    }
    Write-Host "  OK $Tool installe avec succes" -ForegroundColor Green
}

# ─────────────────────────────────────────────
# ETAPE 1 — Outils requis
# ─────────────────────────────────────────────
Write-Host "[ 1/8 ] Verification des outils requis..." -ForegroundColor White

if (-not (Get-Command "winget" -ErrorAction SilentlyContinue)) {
    Write-Host "  X winget n'est pas disponible sur cette machine." -ForegroundColor Red
    Write-Host "    Mets a jour Windows ou installe 'App Installer' depuis le Microsoft Store."
    Write-Host "    https://apps.microsoft.com/detail/9NBLGGH4NNS1"
    exit 1
}
Write-Host "  OK winget disponible" -ForegroundColor Green

Install-IfMissing "git"    "Git.Git"            "https://git-scm.com"
Install-IfMissing "node"   "OpenJS.NodeJS.LTS"  "https://nodejs.org"
Install-IfMissing "python" "Python.Python.3.13" "https://python.org"
Install-IfMissing "curl"   "cURL.cURL"          "https://curl.se"

# npm est embarque avec node — verifier quand meme
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Reload-Path
    if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
        Write-Host "  X npm introuvable apres installation de Node." -ForegroundColor Red
        Write-Host "    Ferme et rouvre ce terminal, puis relance le script."
        exit 1
    }
}
Write-Host "  OK npm disponible" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 2 — Clone du repo
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 2/8 ] Clonage du repo..." -ForegroundColor White

$DefaultDir = "$HOME\Dev\Bissi"
$ProjectDir = if ($env:BISSI_INSTALL_DIR) { $env:BISSI_INSTALL_DIR } else { $DefaultDir }

New-Item -ItemType Directory -Force -Path $ProjectDir | Out-Null
Set-Location $ProjectDir

$RepoUrl = "https://github.com/Smart-Learn-Squad/bissi.git"

if (Test-Path "bissi") {
    Write-Host "  ! Le repo existe deja. On continue." -ForegroundColor Yellow
    Set-Location "bissi"
} else {
    git clone $RepoUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  X Echec du clonage" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK Repo clone" -ForegroundColor Green
    Set-Location "bissi"
}

# ─────────────────────────────────────────────
# ETAPE 3 — Virtualenv Python
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 3/8 ] Creation du virtualenv Python..." -ForegroundColor White

if (Test-Path ".venv") {
    Write-Host "  ! .venv existe deja. On reutilise." -ForegroundColor Yellow
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  X Echec de la creation du virtualenv" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK .venv cree" -ForegroundColor Green
}

# Debloquer l'execution des scripts si necessaire
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq "Restricted" -or $policy -eq "Undefined") {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-Host "  OK ExecutionPolicy mise a jour (RemoteSigned)" -ForegroundColor Green
}

& ".venv\Scripts\Activate.ps1"
Write-Host "  OK Virtualenv active" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 4 — huggingface-cli
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 4/8 ] Installation de huggingface-cli..." -ForegroundColor White

pip install huggingface-hub -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Echec de l'installation de huggingface-hub" -ForegroundColor Red
    exit 1
}
Write-Host "  OK huggingface-cli installe" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 5 — npm install
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 5/8 ] Installation des dependances npm..." -ForegroundColor White

Set-Location "bissi-master-ui"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Echec de npm install" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Dependances npm installees" -ForegroundColor Green
Set-Location ..

# ─────────────────────────────────────────────
# ETAPE 6 — Telechargement modele
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 6/8 ] Telechargement du modele IA (~3 GB)..." -ForegroundColor White
Write-Host "        Cela peut prendre plusieurs minutes. Ne fermez pas ce terminal."
Write-Host ""

New-Item -ItemType Directory -Force -Path "models" | Out-Null

huggingface-cli download unsloth/gemma-4-E2B-it-GGUF `
    gemma-4-E2B-it-Q4_K_M.gguf `
    --local-dir ./models `
    --local-dir-use-symlinks False

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Echec du telechargement du modele" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Modele telecharge dans .\models\" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 7 — Ouverture VS Code
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 7/8 ] Ouverture de VS Code..." -ForegroundColor White

if (Get-Command "code" -ErrorAction SilentlyContinue) {
    code .
} else {
    Write-Host "  ! VS Code non trouve. Ouvre le dossier manuellement." -ForegroundColor Yellow
}

# ─────────────────────────────────────────────
# ETAPE 8 — Lancement
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ 8/8 ] Lancement de Bissi..." -ForegroundColor White
& ".\start.ps1"
