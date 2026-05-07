# BISSI Backend (Gemma 4 Good)

Backend local-first pour un agent autonome Gemma 4 (Ollama), conçu pour une UI Electron via API FastAPI locale.

## Objectif

Ce repo fournit le moteur backend de BISSI pour le hackathon **Gemma 4 Good**:
- exécution locale (privacy-first),
- agent avec tool-calling,
- mémoire persistante locale,
- API SSE prête à brancher à une UI Electron.

## Stack

- Python 3.11+
- Ollama + modèle `gemma4:e2b`
- FastAPI + Uvicorn
- SQLite (conversations)
- ChromaDB (vecteurs)

## Structure

```text
bissi/
├── main.py
├── requirements.txt
├── api/
│   └── server.py
├── core/
│   ├── agent.py
│   ├── engine.py
│   ├── context.py
│   ├── config.py
│   ├── router.py
│   ├── types.py
│   ├── user_profile.py
│   └── memory/
│       ├── conversation_store.py
│       └── vector_store.py
├── onboarding/
│   ├── profile.py
│   └── greeting.py
├── configs/
└── functions/
```

## Prérequis

1. Installer et lancer Ollama.
2. Télécharger le modèle attendu:

```bash
ollama pull gemma4:e2b
```

3. Créer un environnement Python puis installer les dépendances:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

Au démarrage, le backend:
1. vérifie la disponibilité d’Ollama,
2. vérifie la présence du modèle `gemma4:e2b`,
3. lance l’API sur `http://127.0.0.1:8765`.

## API

### `GET /health`
Retourne l’état moteur/modèle.

### `GET /tools`
Retourne la liste des tools agent.

### `GET /conversations`
Retourne les conversations récentes.

### `GET /conversations/{id}/history`
Retourne l’historique complet d’une conversation.

### `DELETE /conversations/{id}`
Supprime une conversation.

### `POST /chat` (SSE)
Body JSON:

```json
{
  "message": "Analyse ce fichier et fais un résumé",
  "conversation_id": null
}
```

Events SSE émis:
- `thinking`
- `tool_start`
- `tool_done`
- `chunk`
- `done`
- `error`

## Exemple rapide (curl)

```bash
curl -N -X POST "http://127.0.0.1:8765/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"Bonjour BISSI","conversation_id":null}'
```

```bash
curl "http://127.0.0.1:8765/health"
```

## Comportement agent

`core/agent.py` applique une boucle en phases:
- verrou de concurrence,
- pré-thinking (`<think>...</think>` extrait et résumé),
- itérations tool-calls avec validation d’arguments,
- fallback de synthèse finale si limite d’itérations atteinte,
- sauvegarde de réponse en mémoire conversationnelle.

## Données locales

Fichiers locaux dans `~/.bissi/`:
- `conversations.db`
- `profile.json`

## Notes

- Le backend est conçu pour un usage localhost (pont UI Electron).
- Les erreurs sont normalisées côté API pour éviter les crashes UI.
- Le repo est orienté robustesse de démonstration hackathon, pas infra distribuée.
