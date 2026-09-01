# BISSI — Graphe de compréhension (Phase 1)

Date : 2026-08-31
Intention validée : "Sanity check + mise à jour → stack BISSI tourne de bout en bout
(llama.cpp :8001 → FastAPI :8765 → Electron)."

## Graphe

```
INTENTION : stack BISSI tourne de bout en bout
            (llama.cpp :8001 → FastAPI :8765 → Electron)

                    ┌────────────────────────────────────────────┐
                    │        BLOCAGE #1 : installation Python    │
                    │   requirements.txt → pynput → evdev →      │
                    │   "Python.h: No such file or directory"    │
                    └──────────────┬─────────────────────────────┘
                                  │ retire 6 paquets morts
                    ┌──────────────▼─────────────────────────────┐
                    │ requirements.txt  ← RETIRER (aucun import)  │
                    │  pynput, PyAutoGUI(+chaine), PyQt6(+WebEngine│
                    │  /sip), sse_starlette                       │
                    └──────────────┬─────────────────────────────┘
                                  │ = fin du build C (évite evdev,
                                  │   -200 Mo PyQt6)
                    ┌──────────────▼─────────────────────────────┐
                    │ Version Python : 3.13 présent LOCAL + sudo │
                    │ (pas besoin de pyenv ; recréer .venv 3.13) │
                    └──────────────┬─────────────────────────────┘

 FRONTEND (Design)          BACKEND (Backend)          INFRA (script)
 bissi-master-ui   ──────  core/ agent.py engine.py  ←───  start.sh / bissi-master.sh
   main.js (electron 28)     api/server.py (FastAPI:8765)    scala llama.cpp :8001
   renderer/chat.html        core/config.py  n_ctx=4096 ←─── BUG: 16384 réel
   renderer/onboarding.html  core/memory/{conversation,vector}  install.sh (cwd bug)
   deps npm vendored         functions/ (30 tools)

 Couplages réciproques :
 • agent.py ─HTTP──► llama_cpp_python (:8001)    [gardé]
 • agent.py ─lazy──► chromadb (vector_store)     [gardé]
 • server.py ─lazy─► faster-whisper (/transcribe) [gardé]
 • office/ ─ python-docx/pptx/openpyxl/PyPDF2/pdfplumber/pytesseract [gardés]
 • database/ ── pyodbc + pandas
 • data/ ── numpy/matplotlib (+ seaborn NON déclaré)
 • audio.py ── openai-whisper (NON déclaré, divergent de faster_whisper)

 Problèmes divergents (hors blocage #1) :
  P1. core/config.py n_ctx=4096 ≠ serveur 16384   (corriger la config)
  P2. functions/media/audio.py importe openai-whisper (non déclaré)
  P3. functions/data/analysis.py importe seaborn (non déclaré)
  P4. install.sh ne se repositionne pas dans le repo (start.sh introuvable)
```

## Décisions en attente de validation utilisateur

1. Retirer les 6 paquets morts + recréer .venv en Python 3.13.
2. Gérer P2/P3 (openai-whisper, seaborn) : lazy + message propre (recommandé)
   vs déclarer les deps.
3. n_ctx (P1) : aligner config sur 16384 (recommandé, conforme AGENTS.md serrures)
   vs abaisser le serveur à 4096.

> statut : GRAPHE SOUMIS POUR VALIDATION — phase 2 (plan) pas encore lancée.
