### BISSI (`~/Dev/OFFMODE/bissi/`)
Local AI agent — PyQt6 WebEngine + Ollama + office suite + RAG.

```bash
cd ~/Dev/OFFMODE/bissi
source .venv/bin/activate
python main.py                        # Bissi Master (WebEngine)
python main.py --edition codes        # Bissi Codes (TUI)
python main.py --edition smartlearn   # Bissi SmartLearn (WebEngine, pédago)
python main.py --legacy               # Ancien UI PyQt6 widgets
```

## Architecture (état actuel)
```
bissi/
├── editions/
│   ├── master/
│   ├── codes/
│   └── smartlearn/
├── core/        (partagé)
├── functions/   (partagé)
├── workflows/   (partagé)
├── configs/     (prompts/configs par édition)
├── agent.py     (partagé)
└── main.py      (dispatcher --edition)
```

## Points critiques (priorité produit)
1. **UX cross-éditions**: cohérence visuelle et comportementale incomplète (feedback, onboarding, états vides).
2. **BISSI Codes (TUI)**: manque de features dev-clés (multiline, persistance historique, `/cd`, résultats tools, ergonomie commande).
3. **Master**: trop de jargon exposé (RAG/mémoire/modèle), redondances UI, chemins sensibles en contexte démo.
4. **SmartLearn**: finaliser polish pédagogique (persistences fines, réutilisation suggestions, suppression branding démo par flag).
5. **Robustesse front**: flux asynchrones JS/bridge complexes, risque de régressions sans tests de parcours UI.

## Garde-fous d’implémentation
- Pas de réécriture massive: patches ciblés et réversibles.
- Préserver la séparation par édition (ne pas mutualiser trop tôt).
- Conserver mode offline par défaut.
- Prioriser fiabilité UX sur nouvelles features.

## Typographie (directive)
- **Master + SmartLearn**: `Roboto` recommandé pour le texte UI (lisibilité, neutralité produit).
- **Code/terminal/snippets**: conserver une police monospace (`JetBrains Mono`/équivalent).
- **BISSI Codes (TUI)**: rester 100% monospace (cohérence terminal).
