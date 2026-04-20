# BISSI

> **Optima, immo absoluta perfectio**

BISSI est un assistant IA **local-first**, pensé pour tourner sur la machine de l’utilisateur avec **Gemma 4 via Ollama**. Le projet privilégie l’usage réel, la confidentialité et une UX différente selon le contexte.

## Ce qui est réellement implémenté aujourd’hui

- **Moteur agent local** en Python, avec appel d’outils via Ollama.
- **Trois éditions** :
  - `master` : poste de travail généraliste
  - `codes` : TUI orientée développement
  - `smartlearn` : mode apprentissage
- **Mémoire locale** :
  - historique de conversation en SQLite
  - index vectoriel Chroma pour RAG local
- **Outils utilisables** :
  - lecture/écriture de documents Word, Excel et PowerPoint
  - lecture PDF/OCR
  - lecture/édition de fichiers texte
  - exploration du système de fichiers
  - exécution Python restreinte avec timeout réel
  - presse-papiers
- **Moteur de workflows** local, simple, de style IFTTT

## Positionnement

BISSI n’est pas un framework cloud-first ni une simple interface de chat.

Le projet vise un **assistant personnel local**, capable de :
- travailler avec les fichiers de l’utilisateur,
- produire des artefacts,
- aider au code, aux documents et à l’apprentissage,
- rester exploitable hors ligne autant que possible.

## Éditions disponibles

- **Master** : `python main.py`
- **Codes** : `python main.py --edition codes`
- **SmartLearn** : `python main.py --edition smartlearn`
- **Legacy UI** : `python main.py --legacy`

## Architecture

- `main.py` sélectionne l’édition active.
- `agent.py` contient la boucle principale de raisonnement + tools.
- `core/` regroupe mémoire, moteur Ollama et routage simple.
- `functions/` contient les capacités concrètes exposées à l’agent.
- `ui/` contient les briques PyQt/WebEngine et le bridge frontend.
- `workflows/` fournit l’automatisation locale.

## Prérequis

- Linux ou macOS
- Python 3.11+
- Ollama installé
- modèle `gemma4:e2b` disponible localement
- environnement virtuel `.venv`

## Installation

```bash
cd ~/Dev/OFFMODE/bissi
source .venv/bin/activate
pip install -r requirements.txt
ollama pull gemma4:e2b
```

## Lancement

```bash
python main.py
python main.py --edition codes
python main.py --edition smartlearn
python main.py --legacy
```

## Validation rapide

```bash
source .venv/bin/activate
.venv/bin/pytest -q tests
python scripts/demo_check.py
```

## Parcours de démo recommandés

1. **Master**
   Ouvrir un fichier Excel, demander une synthèse, puis générer un `.docx`.

2. **Codes**
   Lire un fichier source, expliquer un bug, proposer une correction et écrire un fichier texte de sortie.

3. **SmartLearn**
   Charger un document de cours ou un PDF, puis demander une explication pas à pas et un résumé.

## Robustesse terminal (édition `codes`)

L’édition `codes` active des fallbacks ASCII si le terminal ne gère pas correctement certains glyphes Unicode (box drawing, puces, séparateurs).

Pour forcer ce mode en démo :

```bash
BISSI_CODES_ASCII=1 python main.py --edition codes
```

## Limites connues

- L’exécution Python est **restreinte** avec timeout réel, mais ce n’est pas un sandbox OS complet.
- Le projet est actuellement optimisé pour **Gemma 4** en mono-modèle local.
- Certaines briques décrites dans les anciens documents d’architecture restent des pistes d’évolution, pas des composants déjà présents dans le repo.

## Développement

- privilégier des patchs ciblés et réversibles ;
- préserver la séparation entre éditions ;
- éviter les dépendances cloud non nécessaires ;
- garder les changements UI cohérents entre `master` et `smartlearn`.
- la boucle tools (`agent.py`) sérialise maintenant les retours dictionnaire en JSON complet pour conserver toutes les métadonnées (et éviter la perte de `path`, `size`, `task_done`, etc.).

## Licence

MIT License — Smart-Learn Squad

## Attribution

**Lead technique & auteur unique du code : [Sam (goldensam777)](https://github.com/goldensam777)**
