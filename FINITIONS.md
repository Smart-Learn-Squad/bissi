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

---

## Piste future : adaptation Android / iOS

Approche en 2 phases pour limiter le risque :

1. **Phase 1 (rapide)** : mobile = client, moteur BISSI reste sur desktop/serveur local.
   - UI mobile native (SwiftUI + Kotlin/Compose) ou Flutter.
   - API unique pour chat, mémoire et outils.
   - Permet de livrer vite sans réécrire l’inférence.

2. **Phase 2 (offline mobile réel)** : portage on-device de l’inférence.
   - Runtime natif (llama.cpp/Metal sur iOS, NDK sur Android).
   - Modèles plus compacts (Q4/Q5 selon appareils).
   - Mémoire locale par édition (SQLite + vecteur léger).

Architecture long terme recommandée :

- `Core` partagé (orchestration, prompts, mémoire).
- `Inference adapter` par plateforme (Ollama desktop vs runtime mobile).
- `UI clients` séparés (Web/PyQt, Android, iOS).
