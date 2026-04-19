# UI Pro Pass — BISSI (Master / SmartLearn / Codes)

## Contexte
- Repo: `Smart-Learn-Squad/bissi`
- Stack:
  - Desktop: PyQt6 + WebEngine + QWebChannel
  - Web UIs: `editions/master/ui/web`, `editions/smartlearn/ui/web`
  - TUI: `editions/codes/repl.py`
- Architecture à respecter: éditions séparées + composants partagés (`ui/`, `core/`, `agent.py`).

## Objectif
Rendre les 3 interfaces **production-ready** en corrigeant les points UX/UI/robustesse restants, sans casser les flows existants.

## Fichiers interdits
- `**/qwebchannel.js`
- `editions/**/__main__.py`
- `editions/smartlearn/ui/web/assets/css/common.css`

## Périmètre autorisé
### BISSI Codes
- `editions/codes/repl.py`

### BISSI Master
- `editions/master/ui/web/index.html`
- `editions/master/ui/web/app.js`
- `editions/master/ui/web/app.css` (si nécessaire)

### BISSI SmartLearn
- `editions/smartlearn/ui/web/index.html`
- `editions/smartlearn/ui/web/model.html`
- `editions/smartlearn/ui/web/home.html`
- `editions/smartlearn/ui/web/resume.html`
- `editions/smartlearn/ui/web/assets/js/model.js`
- `editions/smartlearn/ui/web/assets/js/home.js`
- `editions/smartlearn/ui/web/assets/js/resume.js`
- `editions/smartlearn/ui/web/assets/css/model.css`
- `editions/smartlearn/ui/web/assets/css/home.css`
- `editions/smartlearn/ui/web/assets/css/resume.css`

### Shared (uniquement si indispensable)
- `ui/bridge.py`
- `ui/renderers/*`
- `ui/parser.py`

## État déjà en place (à vérifier avant de supposer)
- SmartLearn quiz: génération JSON + carte interactive + score + persistence.
- Dashboard SmartLearn: lecture `bissi_smartlearn_progress`.
- Persistance chapitres/quiz/temps déjà câblée.
- Parsing markdown/math récemment ajusté.

## Travail demandé (priorité décroissante)

### P1 — BISSI Codes (TUI)
1. Prompt path user-friendly (`~` + basename projet), pas de chemin brut.
2. `Ctrl+L` clear log sans relancer splash (clear != new session).
3. Persistance historique commandes/messages entre sessions dans `~/.bissi/codes_history` (déjà utilisé par PromptSession).
4. Coloration syntaxique réelle des blocs de code.
5. Séparateurs dynamiques selon largeur terminal (pas `─ * 64` hardcodé).
6. Input multiline (Shift+Enter newline, Enter submit).
7. Commande `/cd` (validation + update prompt path).
8. Affichage du résultat des tool calls (succès/erreur + extrait utile).
9. Distinction visuelle réponse normale vs erreur agent.
10. Navigation historique ↑↓ fiable.
11. `/history` moins tronqué (compact/verbose acceptable).
12. `/copy` pour copier la dernière réponse.
13. Suggestion de commande proche sur typo.
14. Gestion propre SIGINT/SIGTERM avec sauvegarde d’état.
15. Option `--no-splash`.

### P2 — BISSI Master (Desktop)
1. Réduire jargon visible (`RAG · ChromaDB`, `memory-count`).
2. Éviter redondance badge modèle.
3. Feedback génération plus explicite que le simple curseur.
4. `Nouvelle session` doit reset visuel immédiatement.
5. Remplacer tout chemin absolu affiché par sa version `~`-relative (workspace path inclus).
6. État onboarding/empty state minimal au premier lancement.

### P3 — SmartLearn (Pédagogique)
1. Retirer branding démo intrusif (`Hack by IFRI 2026`, disclaimers) via flag simple.
2. État vide progression engageant (CTA clair).
3. `repondreCompris()` doit persister un signal exploitable.
4. Suggestions réutilisables après premier message.
5. Message d’erreur “80 caractères” plus actionnable.

## Contraintes d’implémentation
- Modifs chirurgicales, pas de réécriture complète.
- Respecter les APIs QWebChannel existantes.
- Pas de dépendances lourdes non justifiées.
- Conserver le mode offline.
- Pas de suppression de fonctionnalités existantes.
- Si un item nécessite un fichier interdit, documenter le blocage et passer à l’item suivant sans contournement.

## Validation requise (obligatoire)
1. Vérification syntaxique:
   - `python3 -m py_compile` pour les `.py` modifiés
   - `node --check` uniquement sur les JS sans imports Qt.
2. Parcours manuels documentés:
   - SmartLearn: analyse chapitre -> quiz -> score -> reload home -> stats cohérentes
   - Master: nouvelle session + chargement conversation + feedback génération
   - Codes: multiline, `/cd`, `/copy`, history ↑↓, tool result display
3. Aucun warning console bloquant sur parcours nominal.

## Livrables attendus
1. Liste des issues traitées (mapping issue -> fichier/patch).
2. Commit atomique par fichier modifié avec message descriptif.
3. Résultats de validation (commandes + sorties utiles).
4. Liste des items non traités + justification.

## Definition of Done
- Aucune donnée hardcodée visible au runtime pour progression SmartLearn.
- Aucun bouton principal inerte.
- Codes REPL utilisable en mode dev réel (multiline, history, `/cd`, tool outputs).
- Master/SmartLearn lisibles, moins techniques, sans données perso exposées.
- Zéro régression parsing markdown/math.
