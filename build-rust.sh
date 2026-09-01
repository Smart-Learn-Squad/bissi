#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "━━━ BISSI — Build backend Rust ━━━"
echo "Compile le backend Rust (bissi-master-backend) en mode release."
echo "Le binaire remplace à terme uvicorn api.server (:8765)."

# 1. Toolchain Rust requise
if ! command -v cargo &> /dev/null; then
    echo "❌ cargo introuvable. Installe Rust : https://rustup.rs"
    exit 1
fi
if ! command -v rustc &> /dev/null; then
    echo "❌ rustc introuvable (cargo présent mais toolchain incomplète)."
    exit 1
fi
echo "✓ Toolchain Rust : $(rustc --version)"

# 2. Crater présent
if [ ! -d "bissi-master-backend" ]; then
    echo "❌ Dossier bissi-master-backend introuvable. Ce dépôt n'a pas le backend Rust."
    exit 1
fi

# 3. Build release
echo "→ Compilation release en cours (cargo build --release)..."
cd bissi-master-backend
if cargo build --release; then
    BIN="$(pwd)/target/release/bissi-backend"
    echo "✓ Build terminé."
    echo "  Binaire : $BIN"
    echo "  Taille : $(du -h "$BIN" | cut -f1)"
    if command -v file &> /dev/null; then
        echo "  Type : $(file -b "$BIN")"
    fi
else
    echo "❌ Échec de la compilation Rust."
    echo "  Voir messages ci-dessus (cargo)."
    exit 1
fi

echo ""
echo "─── Note ───"
echo "Ce binaire est le squelette du futur backend Rust. Le backend Python"
echo "(uvicorn api.server) reste actif pour l'instant via start.sh — on ne"
echo "bascule le lancement sur ce binaire qu'une fois le port des tools"
echo "terminé (voir .notes/session.md)."
