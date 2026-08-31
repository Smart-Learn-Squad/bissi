#!/bin/bash
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "Bienvenue dans l'installateur de Bissi 🤖"
echo "Voici ce qui va se passer :"
echo "1. Vérification des outils requis"
echo "2. Prise en compte du repo (in place, pas de clone si déjà présent)"
echo "3. Installation des dépendances Python via uv"
echo "4. Installation des dépendances npm"
echo "5. Téléchargement du modèle IA (~3 GB)"
echo "6. Ouverture de VS Code"
echo "7. Lancement de l'application"
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

# uv (gestionnaire de dépendances Python — recommandé). Installé si absent.
if ! command -v uv &> /dev/null; then
    echo "⚠ uv est introuvable. Installation d'uv (astral)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # recharge PATH pour disposer de uv dans cette session
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "❌ Échec de l'installation d'uv. Ajoute-le au PATH puis relance."
        exit 1
    fi
fi
echo "✓ uv trouvé ($(uv --version))"

# ÉTAPE 2 — Repo in place
# On installe DANS le dossier courant. Si le dossier courant est déjà le repo
# (présence de pyproject.toml), on ne clone rien — pas de copie séparée.
REPO_URL="https://github.com/Smart-Learn-Squad/bissi.git"
if [ -f "pyproject.toml" ] && [ -f "start.sh" ]; then
    echo "✓ Dossier courant = dépôt Bissi déjà présent. Installation in place."
elif [ -d "bissi" ] && [ -f "bissi/pyproject.toml" ]; then
    echo "→ Dépôt trouvé dans ./bissi — on y descend."
    cd bissi
elif [ -d "bissi" ]; then
    echo "⚠ ./bissi existe mais ne semble pas contenir un dépôt valide."
    if git -C bissi rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        cd bissi
        echo "  (c'est un dépôt git — on continue dans l'état local, sans pull forcé)"
    else
        echo "❌ ./bissi existe sans être un dépôt git. Déplace-le puis relance."
        exit 1
    fi
else
    echo "→ Aucun dépôt ici. Clonage de Bissi dans le dossier courant..."
    if git clone "$REPO_URL"; then
        echo "✓ Repo cloné dans $(pwd)/bissi"
        cd bissi
    else
        echo "❌ Échec du clonage du repo"
        exit 1
    fi
fi

if [ ! -w "$(pwd)" ]; then
    echo "❌ Dossier non inscriptible : $(pwd)"
    exit 1
fi
echo "✓ Répertoire: $(pwd)"

# ÉTAPE 3 — Dépendances Python via uv (pyproject.toml + uv.lock)
echo "→ Installation des dépendances Python via uv..."
if [ ! -f "pyproject.toml" ]; then
    echo "⚠ pyproject.toml introuvable après détermination du repo — je le vérifie."
    echo "  Assure-toi d'avoir la dernière version (git pull)."
    exit 1
fi

# .venv cassé ? (interpréteur pointant vers un python inexistant) -> on le supprime.
# uv le récréera proprement. Détection : le lien python du venv ne résout vers rien.
VENV_PY=".venv/bin/python"
if [ -L "$VENV_PY" ] && ! "$VENV_PY" --version >/dev/null 2>&1; then
    echo "⚠ .venv cassé (interpréteur introuvable). Suppression pour recréation..."
    rm -rf .venv
fi

# S'assurer qu'un Python 3.13 est disponible pour uv (pyproject.toml exige >=3.13).
if ! uv python find 3.13 >/dev/null 2>&1; then
    echo "→ Python 3.13 introuvable. Installation d'un Python 3.13 géré par uv..."
    if ! uv python install 3.13; then
        echo "❌ Impossible d'obtenir Python 3.13. Installe-le manuellement puis relance."
        exit 1
    fi
fi

if uv sync; then
    echo "✓ Dépendances Python installées (.venv géré par uv)"
else
    echo "❌ Échec de l'installation des dépendances Python"
    exit 1
fi

# ÉTAPE 4 — npm install
echo "→ Installation des dépendances npm..."
if [ ! -d "bissi-master-ui" ]; then
    echo "❌ Dossier bissi-master-ui introuvable. Ce dépôt ne semble pas être Bissi."
    exit 1
fi
cd bissi-master-ui
if npm install; then
    echo "✓ Dépendances npm installées"
else
    echo "❌ Échec de l'installation npm"
    exit 1
fi
cd ..

# ÉTAPE 5 — Téléchargement modèle
echo ""
echo "→ Téléchargement du modèle IA (~3 GB)..."
echo "  Cela peut prendre plusieurs minutes selon votre connexion."
echo "  Ne fermez pas ce terminal."
echo ""

# La CLI hf vient du .venv géré par uv (huggingface_hub).
if [ -f "bissi-gemma4-e2b-Q4_K_M.gguf" ]; then
    echo "✓ Modèle déjà présent à la racine : bissi-gemma4-e2b-Q4_K_M.gguf"
elif uv run hf download samsam8623/bissi-gemma4-e2b-GGUF \
    bissi-gemma4-e2b-Q4_K_M.gguf \
    --local-dir . >/dev/null 2>&1; then
    echo "✓ Modèle téléchargé dans le répertoire racine"
else
    echo "❌ Échec du téléchargement du modèle (source bissi-gemma4-e2b-GGUF)"
    exit 1
fi

# ÉTAPE 6 — Ouverture VS Code
echo ""
echo "→ Ouverture de VS Code..."
if command -v code &> /dev/null; then
    code .
else
    echo "⚠ VS Code non trouvé. Ouvre le dossier manuellement."
fi

# ÉTAPE 7 — Lancement
echo ""
echo "→ Lancement de Bissi..."
echo "  Appuyez sur Ctrl+C pour arrêter."
exec bash start.sh
