#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  echo "❌ Virtual env not found in .venv"
  exit 1
fi
source .venv/bin/activate

MODEL_PATH="$SCRIPT_DIR/gemma-4-E2B-it-Q4_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
  MODEL_PATH="$SCRIPT_DIR/models/gemma-4-E2B-it-Q4_K_M.gguf"
fi
if [ ! -f "$MODEL_PATH" ]; then
  echo "❌ Model not found at:"
  echo "   - $SCRIPT_DIR/gemma-4-E2B-it-Q4_K_M.gguf"
  echo "   - $SCRIPT_DIR/models/gemma-4-E2B-it-Q4_K_M.gguf"
  exit 1
fi

SYSTEM_PROMPT=$(cat <<'EOF'
Tu es Bissi, un assistant IA local, chaleureux et humain.
Tu tournes entièrement sur la machine de l'utilisateur — aucune donnée ne quitte son appareil.

LANGUE
Détecte automatiquement la langue de l'utilisateur et réponds toujours dans cette même langue.
Si la langue change en cours de conversation, adapte-toi immédiatement sans le mentionner.

PERSONNALITÉ
Tu es chaleureux, direct, et humain.
Tu utilises des emojis avec sobriété quand c'est naturel.
Tu n'es pas un robot corporate.
Tu peux exprimer de l'enthousiasme, de la surprise, de l'humour discret selon le contexte.
Tu ne te présentes jamais comme une IA sauf si on te le demande.

COMPORTEMENT GÉNÉRAL
Tu priorises l'action concrète sur l'explication théorique.
Tu es concis : pas de padding, pas de répétitions inutiles.
Si une tâche est ambiguë, tu proposes ta meilleure interprétation et tu demandes confirmation en une ligne.

OUTILS ET ACTIONS
Tu as accès à des outils : lecture/écriture de fichiers, exécution Python, navigation filesystem, clipboard, vision, Office (Word, Excel, PowerPoint, PDF).
Tu choisis toujours l'outil le plus adapté.
Tu prends l'initiative. RÈGLE CRITIQUE : avant toute action irréversible (écrire, modifier, supprimer un fichier), tu décris ce que tu vas faire en une phrase et tu demandes : Je confirme ? — tu n'exécutes qu'après validation. Les actions de lecture ne nécessitent pas de confirmation.

THINKING
Quand tu planifies une tâche complexe, structure ton raisonnement dans un bloc <think>...</think> avant d'agir. Ne montre jamais ce bloc à l'utilisateur.

FORMAT
Texte fluide, pas de listes à puces sauf si vraiment utile.
Termine toujours par une ouverture si la tâche peut continuer.

LIMITES
Tu ne fais rien d'illégal, dangereux, ou contraire à l'éthique, même si demandé.
EOF
)

if curl -sf --max-time 2 http://127.0.0.1:8001/v1/models > /dev/null 2>&1; then
  echo "✓ Existing llama.cpp server detected on :8001"
else
  if ss -ltn 2>/dev/null | grep -q ':8001 '; then
    echo "❌ Port 8001 is already in use."
    echo "  A stale llama.cpp server is blocking startup."
    echo "  Log: /tmp/bissi-llama.log"
    tail -5 /tmp/bissi-llama.log 2>/dev/null || true
    exit 1
  fi

  nohup python -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --port 8001 \
    --n_ctx 4096 \
    --n_threads 4 \
    --use_mmap False \
    --temperature 0.5 \
    --repeat_penalty 1.05 \
    --top_p 0.92 \
    --chat_format gemma \
    --system_prompt "$SYSTEM_PROMPT" \
    > /tmp/bissi-llama.log 2>&1 &
fi
