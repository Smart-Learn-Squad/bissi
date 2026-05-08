#!/bin/bash

echo "Bienvenue dans l'installateur de Bissi 🤖"
echo "Voici ce qui va se passer :"
echo "1. Vérification des outils requis"
echo "2. Installation de huggingface-cli si absent"
echo "3. Création du dossier projet"
echo "4. Clonage du repo GitHub"
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

check_tool "git" "https://git-scm.com"
check_tool "node" "https://nodejs.org"
check_tool "npm" "https://nodejs.org"
check_tool "python" "https://python.org"
check_tool "pip" "https://python.org"
check_tool "curl" "https://curl.se"

# ÉTAPE 2 — huggingface-cli
if ! command -v huggingface-cli &> /dev/null; then
    echo "→ Installation de huggingface-cli..."
    pip install huggingface-hub -q
    echo "✓ huggingface-cli installé"
else
    echo "✓ huggingface-cli déjà installé"
fi

# ÉTAPE 3 — Dossier projet
PROJECT_DIR="$HOME/Dev/Bissi"
if [ -d "$PROJECT_DIR" ]; then
    echo "⚠ Le dossier existe déjà. On continue quand même."
else
    echo "→ Création du dossier $PROJECT_DIR..."
    mkdir -p "$PROJECT_DIR"
    echo "✓ Dossier créé"
fi

cd "$PROJECT_DIR"

# ÉTAPE 4 — Clone du repo
REPO_URL="https://github.com/Smart-Learn-Squad/bissi.git"
if [ -d "bissi" ]; then
    echo "⚠ Le repo existe déjà. On continue quand même."
    cd bissi
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

# ÉTAPE 5 — npm install
echo "→ Installation des dépendances npm..."
cd bissi-master-ui
if npm install; then
    echo "✓ Dépendances npm installées"
else
    echo "❌ Échec de l'installation npm"
    exit 1
fi

# ÉTAPE 6 — Téléchargement modèle
echo ""
echo "→ Téléchargement du modèle IA (~3 GB)..."
echo "  Cela peut prendre plusieurs minutes selon votre connexion."
echo "  Ne fermez pas ce terminal."
echo ""

cd ..
mkdir -p models
if huggingface-cli download unsloth/gemma-4-E2B-it-GGUF \
  gemma-4-E2B-it-Q4_K_M.gguf \
  --local-dir ./models \
  --local-dir-use-symlinks False; then
    echo "✓ Modèle téléchargé dans ./models/"
else
    echo "❌ Échec du téléchargement du modèle"
    exit 1
fi

# ÉTAPE 7 — Ouverture VS Code
echo ""
echo "→ Ouverture de VS Code..."
echo "  VS Code va s'ouvrir sur le projet."
echo "  Ne fermez pas ce terminal, l'application va démarrer."

if command -v code &> /dev/null; then
    code .
else
    echo "⚠ VS Code non trouvé. Ouvre le dossier manuellement."
fi

# ÉTAPE 8 — Lancement
echo ""
echo "→ Lancement de Bissi..."
bash start.sh
