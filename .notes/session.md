# BISSI — Session journal (speed-start)

## Cadrage initial (Phase 0)

**Intention (reformulée et validée par utilisateur) :**
Faire un sanity check complet puis mettre à jour tout BISSI pour que le stack
tourne de bout en bout (llama.cpp :8001 → FastAPI :8765 → Electron), en :
1. Débloquant l'installation Python (échec `evdev`/`Python.h` sur Python 3.14)
2. Corrigeant les scripts d'install/start (`start.sh: No such file or directory`)
3. Adaptant le code Python pour la version cible
4. Mettant à jour le frontend Electron / deps npm

**Réponses utilisateur :**
- Objectif : débloquer install Python + corriger scripts + adapter code 3.14 + frontend
- Version Python : celle recommandée (3.11/3.12 via pyenv), ≥ si possible
- Sudo : OUI disponible
- Portée finale : stack qui tourne de bout en bout (tests qui passent)

**Obstacle majeur identifié (sanity check préalable, log utilisateur) :**
- `evdev` (dépendance transitive de `pynput`) ne compile pas :
  `fatal error: Python.h: No such file or directory`
  → il manque les headers de dev Python (`python3-devel` / `python3-dev`).
- Le venv existant a été créé avec le Python système 3.14, ce qui force la
  recompilation des paquets C (éviter avec des wheels précompilés py311/312).
- `./start.sh: No such file or directory` : l'install.sh clône dans un sous-dossier
  mais ne se repositionne pas dans le repo avant de lancer start.sh.

## Découvertes (contextualisation)

- **LOCAL : `python3` = 3.13.15** (pas 3.14 !). Le log d'install avec `cp314` vient
  probablement d'une autre machine/environnement. Sur la machine locale, cibler
  3.13 est naturel et offre des wheels précompilés pour presque tout.
  → Revoir le venv local s'il a été créé en 3.14 ; sinon le recréer proprement.
- Git : branche `main` à jour avec `origin/main`. `AGENTS.md` modifié (non commité).
  `.agents/` et `.notes/` untracked (ne jamais commiter `.notes` dans le repo).
- requirements.txt == épinglé (==) sur toutes les deps + transitive (pynput, PyQt6
  etc.). `pynput==1.8.1` tire `evdev>=1.3` (Linux) : c'est la cause du build C.
  Sur 3.13, `evdev` a des wheels ? À vérifier.

## Phase 0 — Résultats des 5 passes (notes clés)

### Passe 1 (syntaxe)
- Aucun outil de linting/formattage (ni Python ni JS). Style par discipline : 4 espaces,
  `from __future__ import annotations` systématique, docstrings Google, import ordering
  stdlib→tiers→local, bash `set -euo pipefail`.

### Passe 2 (architecture)
- 3 couches : llama.cpp :8001 (OpenAI-compatible) ← FastAPI :8765 (SSE manuel, pas sse_starlette)
  ← Electron (bissi-master-ui, main.js). `main.py` = health check :8001 puis uvicorn :8765.
- Endpoints : /chat (POST SSE), /conversations, /conversations/{id}/history, /delete,
  /patch title & archive, /health, /tools, /transcribe.
- start.sh : venv → pkill stale → llama :8001 (n_ctx 16384, n_threads 10, no mmap) →
  backend :8765 → `cd bissi-master-ui && npm start`.
- INCOHÉRENCE : `core/config.py` LlamaCppConfig.n_ctx=4096 mais serveur lancé en 16384
  (start.sh:40 et bissi-master.sh:76). AgentConfig.context_token_limit=14000.

### Passe 3 (dépendances) — POINT CRUCIAL
- Deps npm réelles : mammoth ^1.6, xlsx ^0.18.5, pdfjs-dist ^3.11 (vendored, chargées en
  <script>, PAS via node_modules au runtime). electron ^28, electron-builder ^24 (dev).
  Le lockfile racine = placeholder vide (84 octets).
- COUPLAGE backend réel : fastapi, starlette, uvicorn, httpx, pydantic, chromadb (lazy),
  faster-whisper (lazy /transcribe), pyodbc, pandas/numpy/matplotlib, python-docx/pptx/
  openpyxl/PyPDF2/pdfplumber/pytesseract, llama_cpp_python (via `python -m llama_cpp.server`).
- **6 paquets MORTS (aucun import) qui cassent l'install** :
  `pynput` (→evdev, source de l'erreur Python.h), `PyAutoGUI` (+PyScreeze/GetWindow/PyRect/
  MouseInfo/Tweening), `PyQt6` (+WebEngine/sip, ~200 Mo), `sse_starlette`.
  → solution propre : les RETIRER de requirements.txt.
- Couplage divergent : functions/media/audio.py importe `openai-whisper` (pas faster_whisper),
  non déclaré. functions/data/analysis.py importe `seaborn` (lazy, non déclaré).
- Aucun pyproject.toml : version Python nulle part épinglée.

### Passe 4 (patterns)
- `BissiAgent` (core/agent.py) orchestre ; `BissiEngine` (core/engine.py) = wrapper HTTP llm
  threadsafe (RLock + retry backoff). Registre d'outils = dict nom→Callable.
- Config : dataclasses frozen, `DEFAULT_CONFIG` module-level accédé directement (pas injecté).
- SSE : StreamingResponse + asyncio.Queue + run_in_executor ; callbacks via call_soon_threadsafe.
- Tests : unit mockent BissiEngine (`patch.object(__init__, return_value=None)` +
  `health_check`). Integration appellent `available_functions` directement.
  ~26-30 tools.
- fonctions/media : image (PIL), audio (whisper+gTTS+ffmpeg), video (ffmpeg) ; validation
  `validate_path_safety`.

### Passe 5 (intention métier)
- BISSI = agent IA local-first offline, fine-tune Gemma 4 E2B, hackathon Google "Gemma 4 Good".
- Cible : équité numérique + éducation, Afrique de l'Ouest francophone (yoruba "augmenté").
- Flux : onboarding prof → chat SSE → upload fichiers (aperçu tronqué) → dictée /transcribe (fr).
- Valeur : 100% offline/privé sur laptop modeste, "le ChatGPT de l'ère Edge-AI".
- Langue : tuné français (system prompt fr, onboarding fr, transcribe force language="fr").

## Décisions de session (Phase 3 - journal immédiat)

1. **Refonte WS** : ajouter un endpoint WS `/ws` côté backend (FastAPI) reprenant la logique
   SSE. NE PAS toucher au JS/HTML de chat.html (propriété Design, page trop complexe).
   Le WS reste exposé mais NON consommé par le frontend cette session (itération future).
2. **Priorité** : débloquer l'install + faire tourner le stack EN PREMIER, refonte WS ensuite.
3. **Stratégie install** : retirer 6 paquets morts de requirements.txt (pynput, PyAutoGUI+
   chaîne, PyQt6+WebEngine/sip, sse_starlette) + recréer .venv en Python 3.13 (wheels précompilés).
4. **P2/P3** : openai-whisper (audio.py) et seaborn (analysis.py) → lazy + message propre.
5. **P1** : aligner core/config.py n_ctx 4096 → 16384 (serveur réel).

## Décisions de session (suite)

6. **Passer à `uv`** (remplace pip/venv/requirements.txt) : 
   - uv gère mieux les wheels + peut installer sa propre toolchain Python + résout
     vite. Décision STRATÉGIQUE -> implique de restructurer install.sh/start.sh /
     requirements.txt (migration vers pyproject.toml [+ uv.lock] + [uv] deps).
   - Question : garder requirements.txt pour compat ou migrer entièrement vers
     pyproject.toml (PEP 621) + uv.lock ? (à trancher)
7. **Sandbox = Flatpak, pas la machine réelle** : pas de sudo/gcc/cmake/Python.h/dnf/apt.
   Débuter : `llama_cpp_python` ne compile pas ici. On fait le MAX faisable dans le
   sandbox (backend, scripts, WS, tests, PAS llm compile/GGUF), LLM à part sur la
   machine réelle (samuelyevi@fedora, qui a sudo).

8. **Migration complète uv** : pyproject.toml (PEP 621, deps directes + python>=3.13),
   uv.lock, suppression de requirements.txt. install.sh/start.sh réécrits pour uv.
9. **llama_cpp_python** : changer de version pour une qui fournit une wheel Linux
   py3.13 (au lieu de compiler). Réessayer après migration.

## DÉCOUVERTE CLÉ (résout le blocage LLM)

- `llama-cpp-python` est SOURCE-ONLY sur PyPI (même en 0.3.35) -> compile toujours,
  et bloque sans toolchain C/C++ (impossible dans le sandbox, pas de gcc/cmake/sudo).
- SOLUTION : installer via l'index de WHEELS officiel d'abetlen
  `https://abetlen.github.io/llama-cpp-python/whl/cpu`
  -> obtient une wheel précompilée (CPU) POUR PYTHON 3.13, SANS compilateur.
  → Testé + OK : llama_cpp ==0.3.23 importe, `llama_cpp.server` dispo.
- => Conserver le pin `llama-cpp-python==0.3.23` d'origine + extra-index CPU dans uv.

## ÉTAPE 1 — RÉUSSIE

- Migration uv : pyproject.toml (deps directes, python>=3.13), uv.lock (319 pkgs),
  .python-version=3.13, requirements.txt supprimé, ancien .venv pip supprimé.
- `uv sync` → .venv 3.13 complet SANS compilation (wheels précompilées partout).
- llama-cpp-python==0.3.23 via index CPU d'abetlen : connu OK, `llama_cpp.server` importe.
- fastapi/uvicorn/httpx/pydantic/chromadb/faster_whisper : imports OK.

## ÉTAPE 1 — TESTS INITIAUX
- Unit (test_agentic_capabilities) : 25 passés, 1 échec =
  test_vector_store_initialization (s'attend à vector_store != None au ctor, or LAZY ligne 70).
- Integration (test_agentic_integration) : 10 passés, 5 échecs =
  - test_agent_search_files / list_directory / search_and_read / complex_file_manipulation :
    TypeError kwargs fantômes ('dir_path', 'file_pattern') vs vrais params — P4.
  - test_agent_context_persistence : vector_store lazy (même cause que unit).
  => Échecs PRÉEXISTANTS (incohérence tests), PAS régression uv. À corriger étape 3.

## ÉTAPE 2 — RÉUSSIE
- install.sh migré uv : vérif/install uv, `uv sync` (à la place venv+pip+requirements),
  `uv run hf/huggingface-cli` pour le GGUF, `exec bash start.sh`.
- start.sh : ensure .venv via `uv sync` si absent ; launch inchangé.
- Test backend uv : uvicorn api.server:app démarre, `GET /tools` liste les ~30 outils. OK.
- `GET /health` échoue si llama.cpp :8001 absent (BissiEngineError, Connection refused) —
  comportement attendu (main.py exige llama.cpp). À noter : /health lève une erreur
  côté server.py:230 au lieu de renvoyer un JSON clair. (amélioration possible étape 4)
- LLM/GGUF ne peuvent pas être testés ici (sandbox, modèle absent) — à faire sur machine réelle.

## TODO étape 3
- P1 : core/config.py n_ctx 4096 -> 16384
- Correction tests : 
  * unit test_vector_store_initialization (vector_store lazy)
  * integration : kwargs fantômes (dir_path/file_pattern) + vector_store lazy
- P2 : audio.py openai-whisper lazy + msg propre
- P3 : analysis.py seaborn lazy + msg propre

## ÉTAPE 3 — RÉUSSIE
- n_ctx 4096 -> 16384 (core/config.py, cohérent scripts + context_token_limit 14000).
- audio.py : msg d'erreur openai-whisper clarifié (optionnel, uv add openai-whisper).
  Lazy déjà en place (check whiper). 
- analysis.py : seaborn msg clarifié (uv add matplotlib seaborn) ; ajout extra
  [project.optional-dependencies] charting = ["seaborn>=0.13"].
- Tests corrigés (mock engine, sans toucher la logique de test) :
  * unit test_vector_store_initialization -> lazy (None par défaut, honoré en injection).
  * integration : file_pattern= -> query= ; dir_path= -> path= ; vector_store lazy.
- Résultat : unit 26/26, integration 15/15 = 41/41 verts (avant 35/6).

## ÉTAPE 4 — RÉUSSIE (WS exposé, frontend INTACT)
- Refactor api/server.py : extrait _start_agent_job(loop, queue, message,
  conversation_id, files, thinking_enabled) -> partagé SSE /chat + WS /ws.
  Comportement SSE inchangé (vérifié pas de régression).
- @app.websocket("/ws") : reçoit {"message","conversation_id","thinking"},
  pousse events JSON (chunk/tool_start/tool_done/thinking/done/ping), heartbeat 15s.
- Test réel : handshake OK + round-trip done (erreur llama.cpp absent = attendu).
  WS n'apparaît pas dans /openapi.json paths (normal, routage WS séparé starlette).
- N'A PAS touché à chat.html / renderer (propriété Design respectée).

## ÉTAPE 5 — RÉUSSIE (sauf LLM réel, modèle absent du sandbox)
- pytest tests/ = 41 passed.
- /chat SSE : done (conn refused llama.cpp = normal sans modèle).
- /ws : handshake + done.
- GGUF / llama.cpp ne peuvent PAS être testés ici — commande de vérif finale
  à exécuter sur la machine réelle (voir journal suivant / commande envoyée).

## PHASE 3 (post-migration) — RUN SUR MACHINE RÉELLE
### Fichiers
1. install.sh / start.sh (workspace) = version à jour (uv).

### Problèmes rencontrés (machine réelle de l'utilisateur)
- `./install.sh` échouait sur `uv sync` : "No pyproject.toml found". Cause :
  TAILLE du script — il clone vers ~/Dev/Bissi/bissi (clone SÉPARÉ) qui n'a PAS
  les changements uv (non commités dans le workspace /mnt/dev/.../bissi).
  = 2 copies du repo (workspace + ~/Dev/Bissi). Confusion.
- Réponse utilisateur : "Genre dans le dossier dans lequel l'user lance le script"
  -> install.sh réécrit pour INSTALLER IN PLACE (dossier courant), PAS de clone GitHub : 
  * si pyproject.toml+start.sh présents dans CWD -> in place, pas de clone.
  * sinon si ./bissi est un dépôt -> y descend.
  * sinon clone dans CWD.
  * vire l'étape "cd ~/Dev/Bissi".
  * harmonisé avec DECISION : pas de BISSI_INSTALL_DIR, pas de ~/Dev/Bissi.

### Modèle GGUF téléchargé
- Répo trouvé : samsam8623/bissi-gemma4-e2b-GGUF -> bissi-gemma4-e2b-Q4_K_M.gguf (API sibling vérifié).
- 1er essai `hf download` STALLED (0 octet, pas de connexion TCP, warning non-auth).
  => Fix : HF_HUB_DISABLE_XET=1 (désactive backend xet qui stallait).
- Téléchargé : bissi-gemma4-e2b-Q4_K_M.gguf = 3 427 878 080 octets (~3.19 Go),
  magic GGUF v3 confirmé (47 47 55 46). Déposé à la racine du workspace.
- Vitesse ~5 Mo/s => ~15 min.

### Bloqué / à faire sur machine réelle (impossible ici : sandbox Flatpak sans node/npm)
- npm install dans bissi-master-ui (node_modules absent workspace) — OK sur machine réelle.
- Vérif bout en bout (llama.cpp + Electron) — start.sh depuis workspace avec .gguf présent.

## RUN 2 (machine réelle) — .venv cassé
- install.sh in-place OK (détecte le repo).
- Échec uv sync : "No interpreter found for Python 3.13" + warning
  ".venv/bin/python3 -> python (interp absent)".
  => Le .venv du workspace (créé en sandbox vers /usr/bin/python3.13) est
  cassé sur la machine réelle (ce /usr/bin/python3.13 n'existe pas là-bas).
- Fix dans install.sh (étape 3 durcie) :
  * si .venv/bin/python est un lien mort -> rm -rf .venv.
  * si `uv python find 3.13` échoue -> `uv python install 3.13`.
  * puis uv sync.
- Commands uv validés en sandbox : `uv python find 3.13`, `uv python install 3.13`.
- Action utilisateur : RELANCER ./install.sh (s'auto-répare). Fallback manuel :
    rm -rf .venv && uv python install 3.13 && uv sync

## RUN 3 (machine réelle) — llama.cpp ne démarre pas
- install.sh in-place OK, uv sync OK (après fix .venv cassé), npm OK, modèle présent.
- Échec : llama.cpp :8001 "ModuleNotFoundError: No module named 'sse_starlette'"
  -> llama_cpp.server.app requiert des deps NON déclarées par le wheel CPU
  de llama-cpp-python 0.3.23 : sse-starlette ET starlette-context.
- Fix : ajouté à pyproject.toml + uv.lock :
  * sse-starlette>=2.1
  * starlette-context>=0.3
- Vérifié en sandbox : import llama_cpp.server.app OK, __main__ OK, 41 tests verts.
- Kubernetes : PAS utilisé par nous — dépendance transitive de chromadb (vector store).
  Harmless, on le garde.

## Action utilisateur
- uv sync (depuis le workspace) pour installer sse-starlette + starlette-context,
  puis relancer ./start.sh.

## Décision validée : refonte backend Rust (strategy "Rust backend + llama.cpp sous-processus")
Date: 2026-09-01
- Analyse : ~11,7k lignes Python backend, 26 tools exposés (core.agent available_functions).
- Outils concernés : analyze_chart, analyze_screenshot, delete_file, describe_image,
  edit_text_file, extract_text_from_image, get_clipboard, get_directory_tree,
  get_file_info, get_recent_files, list_directory, move_file, python_runner,
  read_excel, read_pdf, read_pptx, read_text_file, read_word, safe_operator,
  search_by_content, search_files, set_clipboard, write_excel, write_pptx,
  write_text_file, write_word.
- Stratégie retenue : coeur backend Rust (axum 0.8, SSE + WS natifs Tokio) +
  llama.cpp en sous-processus OpenAI-compatible (:8001). Ne pas réécrire l'inférence.
- Crates envisagées : axum (SSE/WS), tokio, serde/serde_json, reqwest (proxy :8001),
  office_oxide (docx/xlsx/pptx natifs Rust), faster-whisper-rs (STT), Qdrant (standalone,
  remplace chromadb). mistral.rs / llama-cpp-4 / Lexmata llama-gguf = à re-évaluer plus tard
  (immatures).
- Contrainte : frontend Electron + ports :8001/:8765 intouchables (AGENTS.md Design owner).
- Précondition stack Python validée : 26/26 tests unitaires verts (uv, Python 3.13).
- Prochaines étapes (todo) : scaffold Rust dans branche dediée (ne pas casser stack Python).

## Scaffold backend Rust livré (branche rust-backend)
Date: 2026-09-01
- Structure créée dans bissi-master-backend/ (crate cargo "bissi-backend"):
  config.rs, llama.rs (client OpenAI-compatible llama.cpp :8001 + agrégation
  tool_calls streamés), agent.rs (boucle chunk/thinking/tool_start/tool_done/
  file_created/done), conversation.rs (JSON ~/.bissi), main.rs (routes /chat
  SSE multipart, /ws, /conversations*, /health, /tools, /transcribe=501),
  tools/ (registre 26 tools + schemas OpenAI + dispatch ; filesystem réel
  list/read/write, office/vision/code/system en stubs "not_ported").
- Commits : c295c28 (scaffold), c1276eb (fix SSE Event + extracteurs axum).
- Limitation SANDBOX documentée : pas de cc/ld, et les binaires natifs
  compilés via rust-lld segfaultent à l'exécution (incompatibilité runtime)
  → la compilation/finalisation DOIT se faire sur la machine réelle :
      cd bissi-master-backend && cargo build --release
- Pistes crates pour le port des tools stubs not_ported :
  office_oxide (docx/xlsx/pptx), lopdf (pdf), arboard (clipboard),
  image + OCR rust (extract_text_from_image), subprocess .venv/python
  (python_runner), faster-whisper-rs (transcribe).
## Action utilisateur (machine réelle)
- cd bissi-master-backend && cargo build --release  (vérifier compilation)
- rappel : sur machine réelle aussi uv sync && ./start.sh pour valider la
  stack Python existante avant de basculer sur le backend Rust.
