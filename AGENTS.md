### BISSI (`~/Dev/OFFMODE/bissi/`)
Local AI agent — PyQt6 WebEngine + Ollama + office suite + RAG.

```bash
cd ~/Dev/OFFMODE/bissi
source venv/bin/activate
python main.py                        # Bissi Master (WebEngine)
python main.py --edition codes        # Bissi Codes (CLI riche)
python main.py --edition smartlearn   # Bissi Smartlearn (WebEngine, pédago)
python main.py --legacy               # Ancien UI PyQt6 widgets
```

#### Plan 3 éditions — à implémenter

**Architecture cible (monorepo) :**
```
bissi/
├── editions/
│   ├── master/          ← WebEngine actuel (ui/web/ déplacé ici)
│   │   ├── __main__.py
│   │   └── ui/web/
│   ├── codes/           ← CLI rich (pas de PyQt6)
│   │   ├── __main__.py
│   │   └── repl.py
│   └── smartlearn/      ← WebEngine reskin pédago
│       ├── __main__.py
│       └── ui/web/
├── core/        (partagé — inchangé)
├── functions/   (partagé — inchangé)
├── workflows/   (partagé — inchangé)
├── configs/     (partagé — prompt override par édition)
├── agent.py     (partagé — inchangé)
└── main.py      ← dispatcher --edition [master|codes|smartlearn]
```

**Décisions :**
| Question | Réponse |
|----------|---------|
| Mémoire | Séparée par édition (SQLite + ChromaDB distincts) |
| Smartlearn tools | Tous les tools (accès complet étudiant) |
| Smartlearn vs Master | Master = pro pur ; Smartlearn = pages éducatives + prompt pédago |
| Bissi Codes | Interface `rich` full-custom (tool cards, tables, status bar, prompt `bissi @ ~/path ›`) |

**Bissi Codes (CLI) — stack :**
- `rich.live` streaming tokens, `rich.table` tableaux, `rich.console` couleurs
- `prompt_toolkit` prompt avec historique
- Commandes : `/new`, `/exit`, `/history`, `/model`, `/help`

**Bissi Smartlearn — différences vs Master :**
- Logo SmartLearn (infinity animé), palette CSS distincte
- Pages éducatives dans welcome screen (absentes de Master)
- Prompt système pédago (résumé, quiz, plan d'étude)

**Étapes :**
1. `main.py` — ajouter dispatcher `--edition`
2. `ui/web_window.py` — paramètre `web_dir` pour pointer vers le bon `ui/web/`
3. `editions/master/__main__.py` — déplace logique WebWindow actuelle
4. `editions/codes/repl.py` — REPL rich (~150 lignes)
5. `editions/smartlearn/ui/web/` — fork `ui/web/` + reskin CSS + prompt override
6. `configs/prompts.py` — prompts par édition
