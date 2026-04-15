# BISSI — Research Roadmap : MoE Upcycling

> Roadmap post-hackathon (après le 18 mai).
> Objectif : convertir gemma4:e2b et e4b (denses) en architectures MoE
> via upcycling des poids GGUF — sans réentraîner from scratch.

---

## Bibliothèque fondatrice (ordre de lecture)

### 1. Sparse Upcycling — Google Brain (Komatsuzaki, 2023)
**Le papier originel. Point de départ obligatoire.**

- **Lien** : https://arxiv.org/abs/2212.05055
- **Contribution** : Dense checkpoint (T5, ViT) → MoE sparse.
  Démontre qu'on peut upcycler un modèle dense en MoE en
  copiant les poids FFN comme experts initiaux + fine-tuning léger.
- **À retenir** : Le coût de l'upcycling est ~20% du coût d'un
  entraînement dense from scratch pour des performances supérieures.

---

### 2. Upcycling LLMs into MoE — NVIDIA (2024) ← PRIORITÉ
**Le plus avancé sur les poids. Lire en premier après le fondateur.**

- **Lien** : https://arxiv.org/abs/2410.07524
- **Contribution** :
  - Schéma d'initialisation **"virtual group"** — split intelligent des
    matrices FFN en N experts sans effondrement de performance
  - **Weight scaling** adapté à l'upcycling MoE fine-grained
  - Résultats : Nemotron-4 15B upcyclé → **67.6% MMLU**
    vs 65.3% pour le dense continued training
- **Code disponible** — chercher le repo NVIDIA NeMo
- **Pertinence pour BISSI** : C'est exactement ce dont on a besoin
  pour gemma4:e2b/e4b. Virtual group init = méthode pour éviter
  l'effondrement mentionné dans notre analyse GGUF.

---

### 3. BAM! — Beyond FFN (2024)
**Upcycling au-delà des couches FFN.**

- **Lien** : https://arxiv.org/abs/2408.08274
- **Contribution** : Ne se limite pas aux FFN — upcycle aussi les
  paramètres **attention** en Mixture of Attention layers.
  Testé sur 590M → 2B paramètres.
- **Pertinence** : Directement dans la gamme de e2b (2B) et e4b (4B).
  Si on veut aller plus loin que le FFN-only, c'est le papier de référence.

---

### 4. UpIT — Data-Efficient Upcycling (2024)
**Pour contourner le besoin d'un gros corpus.**

- **Lien** : https://arxiv.org/abs/2410.01610
- **Contribution** :
  - Utilise les **checkpoints intermédiaires** du fine-tuning comme
    experts naturellement spécialisés
  - Algorithme génétique + parameter merging pour assurer la diversité
  - Réduit drastiquement le besoin en données d'entraînement
- **Pertinence** : Contexte offline BISSI — pas de gros corpus disponible.
  UpIT est l'approche la plus réaliste pour nous.

---

### 5. PEER — Google DeepMind (2024)
**La vision long terme — 1M+ experts.**

- **Lien** : https://arxiv.org/abs/2407.04153
- **Contribution** : MoE fine-grained avec **plus d'un million d'experts**
  via product key retrieval. Outperform les dense FFW et MoE coarse-grained
  sur le tradeoff performance/compute.
- **Pertinence** : Vision horizon 2026+. Pas d'implémentation immédiate,
  mais oriente l'architecture cible à long terme.

---

## Ce qu'on cherche dans les poids GGUF

Tenseurs FFN dans chaque bloc transformer (à extraire avec `gguf-py`) :

```
blk.N.ffn_gate.weight   → shape (ffn_dim, hidden_dim)
blk.N.ffn_up.weight     → shape (ffn_dim, hidden_dim)
blk.N.ffn_down.weight   → shape (hidden_dim, ffn_dim)
```

### Virtual Group Initialization (méthode NVIDIA — papier 2)

Pour N experts à partir d'un FFN dense :

```
ffn_gate.weight (ffn_dim × hidden_dim)
        ↓  split en N groupes de (ffn_dim/N × hidden_dim)
ffn_gate_exps.weight[0]  ...  ffn_gate_exps.weight[N-1]
```

Même chose pour `ffn_up` et `ffn_down`.
Ajouter ensuite :
```
blk.N.ffn_gate_inp.weight  → shape (hidden_dim, N)  ← routeur, init aléatoire
```

Mettre à jour les métadonnées GGUF :
```
gemma4.expert_count      = N
gemma4.expert_used_count = K   (top-K actifs par token, typiquement K=2)
```

---

## Leviers d'inférence locale pour Gemma 4

Objectif pratique : **le plus puissant possible, sans connexion, sur matériel modeste**.

### 1. Quantization agressive

- **Sources utiles** :
  - GPTQ — [arXiv:2210.17323](https://arxiv.org/abs/2210.17323)
  - QuIP — [arXiv:2307.13304](https://arxiv.org/abs/2307.13304)
- **Idée** : viser des poids 2–4 bits pour réduire RAM et latence.
- **Note pratique** : les formats GGUF `Q4_K_M`, `Q3_K_M`, `Q2_K`, `IQ2_XS`
  viennent surtout de la chaîne `llama.cpp` / `ggml` ; les papiers ci-dessus
  donnent le socle scientifique pour le post-training quantization.

### 2. Speculative decoding

- **Source** : Speculative Sampling — [arXiv:2302.01318](https://arxiv.org/abs/2302.01318)
- **Idée** : un petit draft model propose, le grand modèle valide.
- **Impact attendu** : accélération nette de l'inférence sans modifier le modèle
  principal.

### 3. Context window management

- **Sources utiles** :
  - RAG — [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
  - Lost in the Middle — [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
- **Idée** : garder un contexte actif court (par ex. ~2K tokens) et récupérer
  seulement les chunks nécessaires depuis ChromaDB.
- **Conclusion** : le long contexte brut n'est pas fiable ; la récupération
  ciblée reste la meilleure option offline.

### 4. Fine-tuning LoRA ciblé

- **Sources utiles** :
  - LoRA — [arXiv:2106.09685](https://arxiv.org/abs/2106.09685)
  - QLoRA — [arXiv:2305.14314](https://arxiv.org/abs/2305.14314)
- **Idée** : adapter Gemma 4 aux tâches Bissi (fichiers, documents, Python,
  office, raisonnement local) avec peu de paramètres entraînables.
- **Intérêt** : spécialisation forte pour peu de coût GPU.

### Corpus local recommandé

`papers/` doit contenir les PDFs de référence pour lecture hors-ligne :

1. `GPTQ` — 2210.17323
2. `QuIP` — 2307.13304
3. `Speculative Sampling` — 2302.01318
4. `RAG` — 2005.11401
5. `Lost in the Middle` — 2307.03172
6. `LoRA` — 2106.09685
7. `QLoRA` — 2305.14314

---

## État actuel de BISSI vs roadmap

| Étape | Status | Description |
|---|---|---|
| Software MoE (router heuristique) | ✅ Fait | `core/router.py` — e2b vs e4b selon complexité |
| Mémoire sémantique active | ✅ Fait | `core/user_profile.py` — threshold adaptatif |
| Ouverture GGUF | 🔬 Recherche | Tenseurs lisibles, structure dense confirmée |
| Virtual group init (NVIDIA) | 📅 Post-hackathon | Lire papier 2 en priorité |
| Fine-tuning MoE | 📅 Post-hackathon | Nécessite GPU + données |
| BAM! (attention MoE) | 📅 Long terme | Après validation FFN MoE |
| PEER architecture | 📅 Horizon 2026+ | Vision finale |

---

## Prochaines étapes concrètes (post 18 mai)

1. Lire papier NVIDIA (2) + cloner le repo NeMo pour le code
2. Extraire les tenseurs FFN de gemma4:e2b avec `gguf-py`
3. Implémenter virtual group init sur 1-2 blocs (proof of concept)
4. Tester avec llama.cpp avant de rebuilder le GGUF complet
5. Identifier un dataset minimal pour le fine-tuning (UpIT approach)

---

> *"Optima, immo absoluta perfectio"* — Smart-Learn Squad
