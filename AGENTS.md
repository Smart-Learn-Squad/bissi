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

## Points frontend encore à finaliser

### En cours

- **Upload** : bouton de pièce jointe à fiabiliser de bout en bout.
- **Audio** : enregistreur à brancher sur un vrai flux micro.
- **Thinking** : affichage à rendre plus lisible et cohérent.
- **Nom de l’utilisateur** : footer à synchroniser avec le profil réel.

### Proposition de solution

- **Upload** : garder `file picker + drag/drop + paste`, envoyer les fichiers avec `FormData`, et afficher une prévisualisation minimale avant envoi.
- **Audio** : utiliser `MediaRecorder` côté renderer, puis envoyer le flux enregistré vers le backend via IPC ou `fetch` selon la route retenue.
- **Thinking** : lier l’état visuel au streaming SSE et séparer clairement “thinking”, “tool trace” et “réponse finale”.
- **Nom de l’utilisateur** : lire `profile.json` au chargement, dériver un fallback sûr depuis `first_name`, `last_name`, `display_name`, `username` ou `email`, puis afficher ce nom dans le footer.

### Référence

`@tobiamadou-eng` : prise en charge de ces points frontend.
