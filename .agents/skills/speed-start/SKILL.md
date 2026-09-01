---
name: speed-start
description: Protocole structuré pour démarrer ou reprendre une session de travail sur un projet de code avec votre pair de programmation IA. Déclenche ce skill à chaque fois que Péniel démarre un nouveau projet ou reprend un projet existant avec son pair de code, même s'il ne dit pas explicitement "grooming" ou "session" — des phrases comme "on reprend le projet X", "je veux avancer sur Y", "commençons une session sur ce repo" doivent le déclencher.
---

# Speed-Start Grooming

## Pourquoi ce protocole

Une session de code sans cadrage mène à du code qui répond à une intention mal comprise, ou à des décisions perdues d'une session à l'autre. Ce protocole force un cadrage explicite avant d'écrire une ligne de code, et laisse une trace exploitable (`.notes/`) pour reprendre le fil plus tard sans tout redemander.

## Phase 0 — Cadrage

1. **Demander l'intention** à l'utilisateur et la reformuler pour confirmer qu'elle est bien comprise avant de continuer.
2. **Lire la codebase en 5 passes**, chaque passe avec un angle différent (ce n'est pas 5 lectures identiques) :
   - Passe 1 — Syntaxe : langages utilisés, conventions de style, linting.
   - Passe 2 — Architecture : découpage en modules/dossiers, points d'entrée.
   - Passe 3 — Dépendances : librairies, versions, couplages entre modules.
   - Passe 4 — Patterns : idiomes récurrents, choix de design déjà en place.
   - Passe 5 — Intention métier : ce que le code accomplit réellement, au-delà de sa structure.

## Phase 1 — Compréhension

Produire un **graphe de compréhension** (texte ou mermaid) qui relie : intention utilisateur ↔ modules concernés ↔ dépendances impliquées. Le soumettre à l'utilisateur pour validation avant de continuer.

Sauvegarder ce graphe dans `.notes/comprehension.md`.

## Phase 2 — Planification

Produire un plan que l'utilisateur va valider. Sous chaque étape du plan, suggérer une façon optimale de la réaliser (pas juste "quoi faire" mais "comment le faire bien").

Une fois validé, sauvegarder le plan final dans `.notes/plan.md`.

## Phase 3 — Exécution

À chaque décision prise pendant la session (choix technique, écart par rapport au plan, optimisation trouvée en cours de route), la noter immédiatement dans `.notes/session.md`. Ne pas attendre la fin de la session pour journaliser — la décision doit être notée au moment où elle est prise.

## Phase 4 — Clôture

En fin de session, relire l'intégralité de `.notes/` et produire un fichier `.session.pfm` qui résume la session, selon le format ci-dessous.

## Format `.pfm`

Utiliser TOUJOURS ce format exact :

```pfm
[INTENT]
# Intention de l'utilisateur, reformulée

[STACK]
# Langages / frameworks / outils utilisés dans la session

[STRUCTURE]
# Arborescence du projet
# Si le projet est volumineux, ne lister que les dossiers principaux

[PLAN]
1. ...
   OPS: ... # optimisation appliquée pendant la session, si applicable
2. ...
   OPS: ...

[COLOR: TBD]
# Placeholder — coloration du fichier pas encore implémentée (itération future)

date: YYYY-MM-DD

[Session Performance]
# Barre de progression calculée avec la formule ci-dessous
```

**Formule de performance :**

$$Performance = \frac{\text{Nombre d'étapes réalisées}}{\text{Nombre total d'étapes}}$$

Afficher le résultat sous forme de barre (ex. `[███████---] 70%`).
