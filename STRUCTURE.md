# BISSI - Smart-Learn Squad
# Structure complète d'un Agent Bureau Local (Offline AI Agent)

```
bissi/
│
├── main.py                          # Point d'entrée : Lance l'interface PyQt6
├── manager.py                       # Orchestrateur central (UI ↔ Core ↔ Tools)
├── requirements.txt                 # Dépendances Python
├── .gitignore
├── README.md
│
├── configs/                         # Mémoire & Paramètres globaux
│   ├── __init__.py
│   ├── settings.py                  # Sélection modèle, chemins, logs
│   ├── prompts.py                   # Prompts système BISSI
│   ├── personas/                  # Personnalités spécialisées
│   │   ├── __init__.py
│   │   ├── researcher.py
│   │   ├── student.py
│   │   └── office_assistant.py
│   └── constants.py                 # Constantes globales
│
├── core/                            # Cerveau technique
│   ├── __init__.py
│   ├── bissi.py                     # Moteur Ollama (interface LLM)
│   ├── memory/                      # Mémoire persistante
│   │   ├── __init__.py
│   │   ├── conversation_store.py    # Historique conversations
│   │   ├── vector_store.py          # Embeddings RAG (ChromaDB/FAISS)
│   │   ├── embeddings.py            # Génération embeddings
│   │   └── cache.py                 # Cache réponses fréquentes
│   ├── planner.py                   # Décomposition tâches complexes
│   ├── context_manager.py           # Gestion contexte conversation
│   └── safety.py                    # Validation actions, sandbox
│
├── functions/                       # Muscles (Capacités spécifiques)
│   ├── __init__.py
│   │
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
│   │   ├── search.py                # Recherche globale (fzf-style)
│   │   ├── operations.py            # CRUD fichiers + confirmations
│   │   ├── watcher.py               # Surveillance changements fichiers
│   │   └── indexer.py               # Index contenu pour recherche rapide
│   │
│   ├── code/                        # Exécution code
│   │   ├── __init__.py
│   │   ├── python_runner.py         # Sandbox Python (pandas, numpy, plot)
│   │   ├── shell.py                 # Commandes shell contrôlées
│   │   ├── process_manager.py       # Liste/tue processus
│   │   └── dependencies.py          # Gestion packages pip
│   │
│   ├── data/                        # Analyse données
│   │   ├── __init__.py
│   │   ├── analysis.py              # Stats descriptives
│   │   ├── visualization.py         # Graphiques (matplotlib/seaborn)
│   │   ├── database.py              # SQLite CRUD
│   │   ├── formats.py               # CSV, JSON, Parquet, XML
│   │   └── transformers.py          # Nettoyage/transformation données
│   │
│   ├── web/                         # Web & API (si connectivité)
│   │   ├── __init__.py
│   │   ├── search.py                # Moteur recherche web
│   │   ├── fetch.py                 # Récupération contenu URL
│   │   ├── api_client.py            # Client REST générique
│   │   └── local_index.py           # Index contenu web sauvegardé
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
│   │   ├── screenshot.py            # Capture écran
│   │   ├── notifications.py         # Notifications locales
│   │   ├── automation.py            # Macros, raccourcis clavier
│   │   └── scheduler.py             # Tâches planifiées (cron-like)
│   │
│   └── templates/                   # Génération documents
│       ├── __init__.py
│       ├── engine.py                # Moteur templates Jinja2
│       ├── repository.py            # Stockage templates
│       └── variables.py             # Extraction variables dynamiques
│
├── ui/                              # Interface utilisateur PyQt6
│   ├── __init__.py
│   ├── main_window.py               # Fenêtre principale
│   ├── chat_widget.py               # Zone conversation
│   ├── file_drop.py                 # Drag & drop fichiers
│   ├── toolbar.py                   # Barre outils rapide
│   ├── settings_dialog.py           # Panneau configuration
│   └── styles/                      # Thèmes CSS/QSS
│       ├── light.qss
│       └── dark.qss
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
├── tests/                           # Tests unitaires & intégration
│   ├── __init__.py
│   ├── conftest.py
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

## Modules prioritaires (ordre implémentation)

1. **Office** (Word/Excel/PDF) - Core use case étudiants
2. **Filesystem** (Explorer/Search) - Navigation indispensable
3. **Code** (Python sandbox) - Analyses data
4. **Memory** (Vector store) - RAG pour contexte persistant
5. **Data** (DB/Formats) - Manipulation données structurées
6. **System** (Clipboard/Screenshot) - Intégration OS
7. **Communication** (Email/Calendar) - Productivité complète
8. **Web** - Connexion optionnelle
9. **Media** - Traitement avancé fichiers
10. **Workflows** - Automations avancées
