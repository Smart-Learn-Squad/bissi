## BISSI

Répertoire : `~/Dev/OFFMODE/bissi`

BISSI est un assistant IA **local-first** orienté poste de travail personnel. Le projet tourne principalement avec **Gemma 4 via Ollama**, en Python, avec plusieurs éditions UI :

- `master` : usage quotidien généraliste
- `codes` : terminal/TUI pour dev
- `smartlearn` : apprentissage/pédagogie
- `legacy` : ancienne UI PyQt widgets

Ce document sert de guide aux agents de code qui interviennent dans ce repo.

## Commandes utiles

```bash
cd ~/Dev/OFFMODE/bissi
source .venv/bin/activate

python main.py
python main.py --edition codes
python main.py --edition smartlearn
python main.py --legacy

.venv/bin/pytest -q tests
python scripts/demo_check.py
```

## Positionnement produit

BISSI n’est pas un framework cloud-first ni une plateforme multi-tenant.

Le projet doit rester :

- **local-first**
- **mono-machine**
- **orienté usage réel**
- **simple à lancer**
- **crédible en démo**

Quand un agent hésite entre “plus de puissance” et “plus de fiabilité”, il doit choisir **la fiabilité produit**.

## Architecture actuelle

Les zones les plus importantes :

- `main.py`
  Dispatcher des éditions
- `agent.py`
  Boucle principale agent + registre de tools
- `core/`
  moteur Ollama, mémoire, config, heuristiques simples
- `functions/`
  capacités concrètes exposées à l’agent
- `ui/`
  bridge, renderers, WebEngine, TUI
- `editions/`
  variantes d’interface par contexte
- `workflows/`
  automatisation locale simple
- `tests/`
  socle de validation ciblé

Le repo n’est pas encore fortement modularisé. Les agents doivent éviter les refactors massifs si le gain produit n’est pas immédiat.

## Ce qu’un agent peut améliorer sans risque

Zones à faible risque et forte valeur :

- robustesse des renderers
- lisibilité des réponses et états de chargement
- fiabilité des tools fichiers/documents
- tests ciblés
- documentation réaliste
- messages d’erreur clairs
- préflight et scripts de démo

Zones à risque plus élevé :

- grosse refonte de `agent.py`
- changement de paradigme UI
- ajout de dépendances lourdes
- infra distribuée / serveurs / cloud
- pseudo-sandbox non maîtrisé

## Garde-fous obligatoires

1. **Pas de sur-promesse**
   Les docs doivent refléter le code réellement présent.

2. **Pas de complexité “plateforme” gratuite**
   Ne pas transformer BISSI en clone de DeerFlow.

3. **Pas de réécriture large si un patch ciblé suffit**
   Préférer des améliorations locales et réversibles.

4. **Pas de dépendance cloud imposée**
   Le mode local reste le chemin principal.

5. **Pas d’opérations destructives implicites**
   Les writes/moves/deletes doivent rester encadrés.

6. **Toujours valider**
   Si un changement touche `agent.py`, `functions/`, `ui/parser.py`, `ui/renderers/`, ou `editions/codes/repl.py`, exécuter au minimum les tests ciblés pertinents.

## Priorités produit

Ordre de priorité recommandé :

1. **Stabilité des parcours de démo**
2. **Robustesse des tools**
3. **Qualité du rendu UI**
4. **Tests ciblés**
5. **Clarté documentaire**
6. **Nouvelles features**

En pratique, une petite amélioration testée vaut plus qu’une grosse feature bancale.

## Édition `codes`

`codes` est l’édition la plus sensible aux détails de rendu terminal.

Règles :

- rester **100% monospace**
- éviter les hypothèses fragiles sur la largeur des glyphes Unicode
- prévoir des fallbacks ASCII pour les éléments décoratifs
- privilégier des rendus robustes plutôt que spectaculaires
- accepter qu’un fallback texte soit préférable à un crash de rendu

Quand un agent travaille sur :

- `ui/parser.py`
- `ui/renderers/rich_text.py`
- `editions/codes/repl.py`

il doit penser :

- markdown imparfait des LLM
- streaming partiel
- fences incomplètes
- nested blocks
- différences de terminal/police/rendu Unicode

## Patterns utiles à reprendre de DeerFlow

Les agents peuvent s’inspirer de DeerFlow, mais sans importer sa complexité infra.

Les patterns utiles sont :

### 1. Séparation plus nette des responsabilités

À reprendre progressivement :

- isoler exécution des tools
- isoler rendu/parsing
- isoler mémoire
- isoler politiques de sécurité/confirmation

But :
réduire la pression sur `agent.py` sans lancer une réarchitecture complète.

### 2. Guardrails autour des tools

BISSI doit continuer à renforcer :

- politiques de confirmation
- retours structurés des tools
- messages d’erreur cohérents
- comportement prévisible sur fichiers et code

### 3. Sandbox honnête

Le modèle DeerFlow à retenir n’est pas “copier l’infra”, mais :

- nommer correctement le niveau de sécurité réel
- isoler l’exécution autant que possible
- distinguer clairement lecture / écriture / exécution

Pour BISSI, cela veut dire :

- rester sur une **restricted execution** claire
- éviter d’appeler “sandbox complet” ce qui ne l’est pas

### 4. Préparation à une architecture plus modulaire

Sans basculer dans LangGraph ou MCP, les agents peuvent préparer le terrain :

- registre de tools plus net
- helpers de normalisation des résultats
- conventions de retour homogènes
- petits modules au lieu de branches géantes

### 5. Discipline documentaire

Très important :

- README réaliste
- structure réelle
- scripts de validation simples
- parcours de démo identifiables

## Stabilité produit : quoi reprendre concrètement de DeerFlow

Si l’objectif est la stabilité produit, les “quelques trucs” à reprendre sont :

1. **Une couche de politiques explicites**
   Exemple : confirmation, sécurité, exécution, fallback rendu.

2. **Une meilleure séparation logique des étapes**
   Exemple : parse → render → fallback au lieu d’un seul bloc implicite.

3. **Des retours tools plus homogènes**
   `success`, `error`, `path`, `size`, `task_done`.

4. **Des scripts de vérification**
   Comme `demo_check.py`, à multiplier seulement si utile.

5. **Des tests petits mais ciblés**
   Pas besoin d’une grosse pyramide de tests, mais il faut verrouiller les briques critiques.

## Ce qu’il ne faut pas importer de DeerFlow

À éviter dans BISSI, sauf besoin explicite :

- Nginx / Gateway / architecture distribuée
- multiplication des services
- surcouche de config trop lourde
- MCP généralisé trop tôt
- sous-agents concurrents partout
- abstraction excessive avant besoin réel

BISSI doit rester plus simple, plus personnel, plus direct.

## Style d’intervention attendu des agents

Quand un agent travaille ici, il doit :

- expliquer brièvement ce qu’il change
- faire des patches ciblés
- vérifier l’impact localement quand c’est possible
- éviter de laisser un repo “plus abstrait mais moins fiable”

Une bonne intervention dans BISSI améliore au moins un de ces axes :

- démo
- fiabilité
- lisibilité
- sécurité pratique
- maintenabilité

## Règle finale

Si un agent doit choisir entre :

- une idée impressionnante,
- ou une amélioration qui rend BISSI plus stable pour un utilisateur réel,

il doit choisir **la stabilité du produit**.
