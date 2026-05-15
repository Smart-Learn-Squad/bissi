# AGENTS.md — Règles de contribution BISSI Master

## Qui fait quoi

| Rôle | Fichiers autorisés |
| --- | --- |
| Design | `bissi-master-ui/renderer/chat.html` · `bissi-master-ui/renderer/onboarding.html` |
| Backend | `core/` · `api/` · `functions/` · `onboarding/` · `main.py` |

## ⛔ NE PAS TOUCHER — Équipe Design

Ces fichiers sont critiques et ne doivent pas être modifiés :

- `core/` — Moteur agent, mémoire, contexte, types
- `api/server.py` — API FastAPI
- `functions/` — Tools de l'agent
- `main.py` — Point d'entrée backend
- `preload.js` — Bridge Electron sécurisé
- `main.js` — Process principal Electron
- `bissi-master.sh` — Lancement llama.cpp
- `requirements.txt`

## ✅ Fichiers design — Ce que vous pouvez modifier

### `renderer/chat.html`

- CSS variables en haut du fichier → couleurs, espacements
- Layout HTML → structure visuelle
- Animations, transitions
- Tailles de police

### `renderer/onboarding.html`

- Même règles que chat.html

### Variables CSS à modifier en priorité

```css
:root {
  --acc: #7C3AED;        /* Couleur d'accent */
  --bg: #0D0D12;         /* Fond principal */
  --sb: #1A1A2E;         /* Sidebar */
  --text: #E2E8F0;       /* Texte principal */
  --muted: ...;          /* Texte secondaire */
}
```

Ce qu'il ne faut PAS modifier dans chat.html:

Les fonctions JavaScript (connexion SSE, fetch, etc.)
Les id et class utilisés par le JS
La structure des éléments interactifs

### Workflow

1. Créer une branche : git checkout -b design/nom-du-changement
2. Modifier uniquement les fichiers autorisés
3. Tester visuellement (npm start)
4. Pull request → review obligatoire avant merge

### En cas de doute

Ne touche pas. Ouvre une issue et demande.

---

## 🔴 Backend non connecté au Frontend — Plan de travail

### HIGH — Priorité haute (nécessite backend + frontend)

#### Canvas / Visionneur de documents (~200-300 lignes)
- **Où** : `chat.html` (l.620-638) + `preload.js` + `main.js`
- **Problème** : Les onglets Document/Données/Code existent, les libs vendor (`mammoth`, `xlsx`, `pdfjs`, `highlight.js`) sont importées, mais **aucun code** ne peuple le canvas.
- **À faire** : Écrire les handlers d'appel IPC `bissi.file.read/readBuffer` depuis le renderer, instancier chaque lib pour le rendu, gérer les états loading/erreur.
- **Réf**: `@tobiamadou-eng`

#### Audio / Enregistrement vocal (~300-400 lignes)
- **Où** : `chat.html` (l.602-609 bouton micro sans handler) + nouvelle route API
- **Problème** : `functions/media/audio.py` existe (Whisper + TTS) mais aucune route REST, pas de `MediaRecorder` côté renderer, pas de flux SSE pour retour audio.
- **À faire** : Nouvel endpoint API + `MediaRecorder` dans renderer + envoi blob → backend → transcription.
- **Réf**: `@tobiamadou-eng`

### MEDIUM — Priorité moyenne (frontend uniquement)

#### Upload fichiers → agent (~50-80 lignes)
- **Où** : `api/server.py:69-81` + `core/agent.py`
- **Problème** : Les fichiers sont reçus par `POST /chat` (FormData) et loggués, mais **jamais passés** à `agent.process_request()`. L'utilisateur attache des fichiers qui ne servent à rien.
- **À faire** : Passer `files` dans `process_request()`, ajouter le paramètre dans la signature de l'agent, lire le texte des fichiers et l'injecter dans le contexte.
- **Réf**: `@tobiamadou-eng`

#### Trace outils SSE (tool_start / tool_done) (~60-100 lignes)
- **Où** : `chat.html` — boucle SSE reader (l.1175-1197)
- **Problème** : Les events `tool_start`/`tool_done` sont émis par le backend (server.py:60-64) mais **ignorés** dans le reader. Les classes CSS existent (`.tool-t`, `.t-verb` l.429-435).
- **À faire** : Ajouter `case 'tool_start'` / `case 'tool_done'` dans le reader SSE, créer des éléments DOM pour chaque outil, gérer le nesting temporel.
- **Réf**: `@tobiamadou-eng`

### LOW — Priorité basse (frontend uniquement, déjà faits)

✅ *Erreurs SSE* — Connecté (bannière #error-banner + handler SSE)
✅ *Thinking SSE* — Connecté (affichage en direct du reasoning)
✅ *Modèle display-only* — Dropdown rendu non-cliquable (info-only)
✅ *Greeting onboarding* — Fixé (consommation correcte du flux SSE POST /chat)

---

## Résultats des tests agent

- `test_e2e_quick.py` démarre bien quand `llama.cpp` et l’API sont en place.
- La réponse simple fonctionne, mais elle peut être lente selon le chargement du modèle.
- Les tool calls sont encore mal remontés côté test rapide : la réponse contient parfois la trace `<|tool_call|>` au lieu d’un vrai appel exécuté.

### Lecture rapide

Le runtime répond, mais l’exécution des outils reste à fiabiliser pour obtenir un cycle agent complet.

`@tobiamadou-eng` : point de suivi sur la fiabilisation des outils et du flux de réponse.
