# BISSI - Smart-Learn Squad
# Structure actuelle du dépôt

```
bissi/
│
├── main.py                          # Point d'entrée : Lance l'interface PyQt6
├── manager.py                       # Dataclasses simples pour éditions/modèles
├── requirements.txt                 # Dépendances Python
├── .gitignore
├── README.md
│
├── configs/                         # Mémoire & Paramètres globaux
│   ├── __init__.py
│   ├── settings.py                  # Réglages généraux
│   ├── prompts.py                   # Prompts système BISSI
│   ├── personas/                    # Personnalités spécialisées
│   │   ├── __init__.py
│   │   ├── researcher.py
│   │   ├── student.py
│   │   └── office_assistant.py
│
├── core/                            # Cerveau technique réellement utilisé
│   ├── __init__.py
│   ├── bissi.py                     # Moteur Ollama (interface LLM)
│   ├── config.py                    # Configuration runtime
│   ├── router.py                    # Heuristiques simples de scoring/routage
│   ├── types.py                     # Types communs
│   ├── user_profile.py              # Profil d'usage local
│   ├── memory/                      # Mémoire persistante
│   │   ├── __init__.py
│   │   ├── conversation_store.py    # Historique conversations
│   │   └── vector_store.py          # Index vectoriel local (Chroma)
│
├── functions/                       # Capacités effectivement présentes
│   ├── __init__.py
│   ├── office/                      # Suite Office complète
│   │   ├── __init__.py
│   │   ├── word.py                  # DOCX read/write/template
│   │   ├── excel.py                 # XLSX formules, graphiques, pivot
│   │   ├── powerpoint.py            # PPTX création, templates
│   │   ├── pdf.py                   # PDF read/OCR/write/edit
│   │   └── ocr.py                   # OCR images/PDFs scannés
│   │
│   ├── filesystem/                  # Système fichiers
│   │   ├── __init__.py
│   │   ├── explorer.py              # Navigation arborescence
│   │   └── writer.py                # Lecture/écriture texte
│   │
│   ├── code/                        # Exécution code
│   │   ├── __init__.py
│   │   └── python_runner.py         # Exécution Python restreinte + timeout
│   │
│   ├── data/                        # Analyse données
│   │   ├── __init__.py
│   │   ├── analysis.py              # Stats descriptives
│   │
│   ├── web/                         # Web & API (si connectivité)
│   │   ├── __init__.py
│   │   ├── search.py                # Moteur recherche web
│   │
│   ├── communication/               # Communication
│   │   ├── __init__.py
│   │   ├── email_client.py          # IMAP/SMTP read/send
│   │   ├── calendar.py              # CalDAV/ICS read/write
│   │   └── contacts.py              # Gestion contacts (vCard)
│   │
│   ├── media/                       # Traitement média
│   │   ├── __init__.py
│   │   ├── audio.py                 # Transcription (Whisper), TTS
│   │   ├── image.py                 # Resize, convert, metadata
│   │   └── video.py                 # Extraction frames, transcription
│   │
│   ├── system/                      # Contrôle système
│   │   ├── __init__.py
│   │   ├── clipboard.py             # Lire/écrire presse-papiers
│   │
│   └── templates/                   # Génération documents
│       ├── __init__.py
│       ├── engine.py                # Moteur templates Jinja2
│       └── repository.py            # Stockage templates
│
├── ui/                              # Interface utilisateur PyQt6 / WebEngine
│   ├── __init__.py
│   ├── agent_worker.py              # Thread de travail agent
│   ├── bridge.py                    # Pont Python ↔ JS
│   ├── main_window.py               # Ancienne UI widgets
│   ├── parser.py                    # Parsing frontend
│   ├── web_window.py                # Fenêtre WebEngine principale
│   └── styles/                      # Thèmes CSS/QSS
│   ├── renderers/                   # Rendu markdown/rich text
│   ├── themes/                      # Système de thème
│   └── web/                         # Assets web partagés
│
├── workflows/                       # Automations chaînées
│   ├── __init__.py
│   ├── engine.py                    # Moteur workflow (IFTTT-style)
│   ├── triggers.py                  # Déclencheurs (fichier, heure, événement)
│   ├── actions.py                   # Actions disponibles
│   └── examples/                    # Workflows prédéfinis
│       ├── report_generator.yaml
│       ├── backup_daily.yaml
│       └── email_digest.yaml
│
├── tests/                           # Tests ciblés sur les briques critiques
│   ├── __init__.py
│   ├── test_core/
│   ├── test_functions/
│   └── test_workflows/
│
└── docs/                            # Documentation
    ├── architecture.md
    ├── api_reference.md
    ├── user_guide.md
    └── examples/

```

## À lire correctement

Ce document décrit la **structure réelle du dépôt aujourd’hui**.

Les anciens éléments de roadmap qui mentionnaient des modules comme
`planner.py`, `context_manager.py`, `shell.py` ou `fetch.py` relevaient d’une
vision d’extension plus large, mais ne doivent pas être présentés comme des
composants déjà implémentés dans cette version.
