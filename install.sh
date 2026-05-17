#!/bin/bash
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "Bienvenue dans l'installateur de Bissi 🤖"
echo "Voici ce qui va se passer :"
echo "1. Vérification des outils requis"
echo "2. Clonage du repo GitHub"
echo "3. Création du virtualenv Python"
echo "4. Installation de huggingface-cli"
echo "5. Installation des dépendances npm"
echo "6. Téléchargement du modèle IA (~3 GB)"
echo "7. Ouverture de VS Code"
echo "8. Lancement de l'application"
echo ""

# ÉTAPE 1 — Vérifications
echo "→ Vérification des outils requis..."

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 n'est pas installé."
        echo "→ Installe-le depuis $2 puis relance ce script."
        exit 1
    else
        echo "✓ $1 trouvé"
    fi
}

check_tool "git"    "https://git-scm.com"
check_tool "node"   "https://nodejs.org"
check_tool "npm"    "https://nodejs.org"
check_tool "python3" "https://python.org"
check_tool "curl"   "https://curl.se"

# ÉTAPE 2 — Clone du repo
PROJECT_DIR="${BISSI_INSTALL_DIR:-$HOME/Dev/Bissi}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

if [ ! -w "$PROJECT_DIR" ]; then
    echo "❌ Dossier d'installation non inscriptible: $PROJECT_DIR"
    echo "→ Définit un dossier writable: export BISSI_INSTALL_DIR=~/Dev/Bissi"
    exit 1
fi

REPO_URL="https://github.com/Smart-Learn-Squad/bissi.git"
if [ -d "bissi" ]; then
    echo "⚠ Le repo existe déjà. On continue quand même."
    cd bissi
    if ! git pull --ff-only; then
        echo "⚠ Impossible de mettre à jour automatiquement le repo (conflit ou historique local)."
        echo "  On continue avec l'état local actuel."
    fi
else
    echo "→ Clonage du repo..."
    if git clone "$REPO_URL"; then
        echo "✓ Repo cloné avec succès"
        cd bissi
    else
        echo "❌ Échec du clonage du repo"
        exit 1
    fi
fi

# ÉTAPE 3 — Virtualenv Python
echo "→ Création du virtualenv Python..."
if [ -d ".venv" ]; then
    echo "⚠ .venv existe déjà. On réutilise."
else
    if python3 -m venv .venv; then
        echo "✓ .venv créé"
    else
        echo "❌ Échec de la création du virtualenv"
        exit 1
    fi
fi

source .venv/bin/activate
echo "✓ Virtualenv activé"

# ÉTAPE 4 — Mise à jour pip + dépendances Python
echo "→ Mise à jour de pip..."
if python3 -m pip install --upgrade pip -q; then
    echo "✓ pip mis à jour"
else
    echo "❌ Échec de la mise à jour de pip"
    exit 1
fi

echo "→ Installation des dépendances Python..."
if python3 -m pip install -r requirements.txt; then
    echo "✓ Dépendances Python installées"
else
    echo "❌ Échec de l'installation des dépendances Python"
    exit 1
fi

echo "→ Installation de huggingface-cli..."
if python3 -m pip install --upgrade huggingface_hub -q; then
    echo "✓ huggingface-cli installé"
else
    echo "❌ Échec de l'installation de huggingface-hub"
    exit 1
fi

# ÉTAPE 5 — npm install
echo "→ Installation des dépendances npm..."
cd bissi-master-ui
if npm install; then
    echo "✓ Dépendances npm installées"
else
    echo "❌ Échec de l'installation npm"
    exit 1
fi
cd ..

# ÉTAPE 6 — Téléchargement modèle
echo ""
echo "→ Téléchargement du modèle IA (~3 GB)..."
echo "  Cela peut prendre plusieurs minutes selon votre connexion."
echo "  Ne fermez pas ce terminal."
echo ""


if hf download samsam8623/bissi-gemma4-e2b-GGUF \
    bissi-gemma4-e2b-Q4_K_M.gguf \
  --local-dir .; then
    echo "✓ Modèle téléchargé dans ./models/"
else
    if command -v hf &> /dev/null; then
        HF_CLI=(hf)
    elif command -v huggingface-cli &> /dev/null; then
        HF_CLI=(huggingface-cli)
    else
        HF_CLI=(python3 -m huggingface_hub.commands.huggingface_cli)
    fi

    if "${HF_CLI[@]}" download unsloth/gemma-4-E2B-it-GGUF \
      gemma-4-E2B-it-Q4_K_M.gguf \
      --local-dir ./models \
      --local-dir-use-symlinks False; then
        echo "✓ Modèle téléchargé dans ./models/"
    else
        echo "❌ Échec du téléchargement du modèle"
        exit 1
    fi
fi

# ÉTAPE 7 — Ouverture VS Code
echo ""
echo "→ Ouverture de VS Code..."
if command -v code &> /dev/null; then
    code .
else
    echo "⚠ VS Code non trouvé. Ouvre le dossier manuellement."
fi

# ÉTAPE 8 — Lancement
echo ""
echo "→ Lancement de Bissi..."
bash start.sh
