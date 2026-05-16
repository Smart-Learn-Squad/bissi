#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Bienvenue dans l'installateur de Bissi " -NoNewline
Write-Host "Robot" -ForegroundColor Cyan
Write-Host "Voici ce qui va se passer :"
Write-Host "1. Verification des outils requis"
Write-Host "2. Clonage du repo GitHub"
Write-Host "3. Creation du virtualenv Python"
Write-Host "4. Installation de huggingface-cli"
Write-Host "5. Installation des dependances npm"
Write-Host "6. Telechargement du modele IA (~3 GB)"
Write-Host "7. Ouverture de VS Code"
Write-Host "8. Lancement de l'application"
Write-Host ""

# ─────────────────────────────────────────────
# ETAPE 1 — Verifications
# ─────────────────────────────────────────────
Write-Host "-> Verification des outils requis..."

function Check-Tool {
    param(
        [string]$Tool,
        [string]$Url
    )
    if (-not (Get-Command $Tool -ErrorAction SilentlyContinue)) {
        Write-Host "X $Tool n'est pas installe." -ForegroundColor Red
        Write-Host "-> Installe-le depuis $Url puis relance ce script."
        exit 1
    }
    Write-Host "OK $Tool trouve" -ForegroundColor Green
}

Check-Tool "git"     "https://git-scm.com"
Check-Tool "node"    "https://nodejs.org"
Check-Tool "npm"     "https://nodejs.org"
Check-Tool "python"  "https://python.org"
Check-Tool "curl"    "https://curl.se"

# ─────────────────────────────────────────────
# ETAPE 2 — Clone du repo
# ─────────────────────────────────────────────
$DefaultDir = "$HOME\Dev\Bissi"
$ProjectDir = if ($env:BISSI_INSTALL_DIR) { $env:BISSI_INSTALL_DIR } else { $DefaultDir }

New-Item -ItemType Directory -Force -Path $ProjectDir | Out-Null
Set-Location $ProjectDir

$RepoUrl = "https://github.com/Smart-Learn-Squad/bissi.git"

if (Test-Path "bissi") {
    Write-Host "! Le repo existe deja. On continue quand meme." -ForegroundColor Yellow
    Set-Location "bissi"
} else {
    Write-Host "-> Clonage du repo..."
    git clone $RepoUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "X Echec du clonage du repo" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK Repo clone avec succes" -ForegroundColor Green
    Set-Location "bissi"
}

# ─────────────────────────────────────────────
# ETAPE 3 — Virtualenv Python
# ─────────────────────────────────────────────
Write-Host "-> Creation du virtualenv Python..."

if (Test-Path ".venv") {
    Write-Host "! .venv existe deja. On reutilise." -ForegroundColor Yellow
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "X Echec de la creation du virtualenv" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK .venv cree" -ForegroundColor Green
}

# Activer le venv
& ".venv\Scripts\Activate.ps1"
Write-Host "OK Virtualenv active" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 4 — huggingface-cli dans le venv
# ─────────────────────────────────────────────
Write-Host "-> Installation de huggingface-cli..."
pip install huggingface-hub -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Echec de l'installation de huggingface-hub" -ForegroundColor Red
    exit 1
}
Write-Host "OK huggingface-cli installe" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 5 — npm install
# ─────────────────────────────────────────────
Write-Host "-> Installation des dependances npm..."
Set-Location "bissi-master-ui"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Echec de l'installation npm" -ForegroundColor Red
    exit 1
}
Write-Host "OK Dependances npm installees" -ForegroundColor Green
Set-Location ..

# ─────────────────────────────────────────────
# ETAPE 6 — Telechargement modele
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "-> Telechargement du modele IA (~3 GB)..."
Write-Host "   Cela peut prendre plusieurs minutes selon votre connexion."
Write-Host "   Ne fermez pas ce terminal."
Write-Host ""

New-Item -ItemType Directory -Force -Path "models" | Out-Null
huggingface-cli download unsloth/gemma-4-E2B-it-GGUF `
    gemma-4-E2B-it-Q4_K_M.gguf `
    --local-dir ./models `
    --local-dir-use-symlinks False

if ($LASTEXITCODE -ne 0) {
    Write-Host "X Echec du telechargement du modele" -ForegroundColor Red
    exit 1
}
Write-Host "OK Modele telecharge dans .\models\" -ForegroundColor Green

# ─────────────────────────────────────────────
# ETAPE 7 — Ouverture VS Code
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "-> Ouverture de VS Code..."
if (Get-Command "code" -ErrorAction SilentlyContinue) {
    code .
} else {
    Write-Host "! VS Code non trouve. Ouvre le dossier manuellement." -ForegroundColor Yellow
}

# ─────────────────────────────────────────────
# ETAPE 8 — Lancement
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "-> Lancement de Bissi..."
& ".\start.ps1"
