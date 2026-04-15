# FINITIONS

Points d’amélioration prioritaires pour Bissi / SmartLearn :

- Séparer plus nettement `bridge`, `parser`, `ui web` et `agent worker`.
- Finaliser les éditions **Master** et **SmartLearn** comme vrais forks isolés.
- Rendre le **stop generation** plus visible et plus réactif.
- Packager tous les assets tiers en local : KaTeX, highlight.js, polices.
- Ajouter des tests ciblés sur le parser temps réel :
  - fences Markdown incomplètes
  - LaTeX
  - langages mixtes
  - interruption de génération
- Uniformiser le rendu streaming / final pour éviter les écarts visuels.
- Améliorer les messages d’erreur UI quand QWebChannel, le modèle ou un tool échouent.
- Optimiser le démarrage en chargeant seulement ce qui est utile à chaque édition.

Priorité recommandée :

1. Stabilisation du streaming
2. Tests du parser
3. Assets locaux 100%
