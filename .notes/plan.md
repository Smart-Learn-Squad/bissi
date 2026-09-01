# BISSI — Plan de session (Phase 2)

Date : 2026-08-31
Statut : VALIDÉ PAR UTILISATEUR

## Intention
Sanity check + mise à jour BISSI → stack tourne de bout en bout, avec refonte
backend en WebSocket préparée (sans toucher au frontend Design).

## Plan

### Étape 1 — Débloquer l'installation Python (HI)
But : `pip install -r requirements.txt` passe, .venv fonctionnel en 3.13.
OPTS:
- Retirer 6 paquets morts de requirements.txt : pynput, PyAutoGUI(+PyScreeze/
  GetWindow/PyRect/MouseInfo/Tweening), PyQt6(+WebEngine/sip), sse_starlette.
  → supprime le build C evdev et ~200 Mo PyQt6, sans casser (aucun import).
- Recréer le .venv en Python 3.13 (wheels précompilés).

### Étape 2 — Corriger les scripts de lancement
But : `./install.sh` puis `./start.sh` lancent la stack.
OPTS:
- install.sh : se repositionner dans le repo avant start.sh (bug start.sh introuvable).
- start.sh : vérifier cd bissi-master-ui && npm start, gestion PIDs, cohérence n_ctx.

### Étape 3 — Nettoyer incohérences backend (sanity restant)
But : code cohérent, tests verts.
OPTS:
- P1 : core/config.py n_ctx 4096 → 16384 (serveur réel).
- P2 : functions/media/audio.py openai-whisper → lazy + msg propre.
- P3 : functions/data/analysis.py seaborn → lazy + msg propre.
- Tests : corriger params fantômes (file_pattern→query, dir_path→path).

### Étape 4 — Exposer un endpoint WebSocket /ws (backend)
But : WS prêt côté serveur, reprend la logique SSE.
OPTS:
- api/server.py : ajouter endpoint WS /ws (websockets).
- Réutiliser la mécanique file asyncio + run_in_executor existante.
- Frontend NON modifié : WS exposé, consommation en itération future.

### Étape 5 — Vérification de bout en bout
But : stack démarre, tests verts.
OPTS:
- pytest unit + integration (sans LLM).
- start.sh / bissi-master.sh si GGUF présent ; sinon installer + backend OK.
- test_e2e_quick.py si llama.cpp dispo (facultatif).
