# BISSI — Soumission Kaggle Gemma 4 Good Hackathon

## Résumé du projet

**BISSI** (Built-In Smart System Intelligence) est un assistant IA personnel de bureau qui tourne **entièrement en local** grâce à **Google Gemma 4** via llama.cpp. Aucune donnée ne quitte la machine de l'utilisateur.

---

## Comment Gemma 4 est utilisé

- **Modèle** : `gemma-4-E2B-it` quantifié en GGUF Q4_K_M (~3 GB)
- **Inférence** : `llama-cpp-python` — serveur OpenAI-compatible local
- **Mode** : streaming SSE avec extended thinking affiché en temps réel
- **Function calling** : l'agent appelle des outils (filesystem, code, bureautique) et envoie les résultats au modèle pour synthèse

---

## Fonctionnalités démontrées

### 1. 🎤 Dictée vocale (Web Speech API)
L'utilisateur parle — le texte apparaît en temps réel dans la zone de saisie. Transcription française, bouton pulse en rouge pendant l'enregistrement.

### 2. 📎 Upload et analyse de documents
Glisser-déposer ou coller un fichier (Word, Excel, PDF, code) → le contenu est automatiquement injecté dans le contexte du modèle. BISSI peut résumer, corriger, analyser.

### 3. 🖼️ Canvas document viewer
Le canvas s'ouvre automatiquement dès qu'un fichier est joint :
- `.docx/.doc` → rendu Word complet (mammoth.js)
- `.xlsx/.xls/.csv` → tableau interactif (SheetJS)
- `.pdf` → rendu des pages (pdf.js)
- Code → coloration syntaxique (highlight.js)

### 4. 🧠 Extended Thinking visible
Le raisonnement interne de Gemma 4 s'affiche en temps réel dans l'interface, permettant à l'utilisateur de suivre le processus de réflexion.

### 5. 🛠️ Agent avec outils
BISSI peut lire/écrire des fichiers, exécuter du Python, créer des fichiers Excel, rechercher sur le disque — tout en local.

### 6. 💬 Mémoire persistante
Toutes les conversations sont stockées en SQLite. Reprise de contexte instantanée.

---

## Impact social (thème Gemma 4 Good)

BISSI démontre qu'une IA puissante peut être :
- **Accessible** : fonctionne sur un laptop standard (CPU)
- **Privée** : données médicales, juridiques, personnelles ne quittent jamais la machine
- **Souveraine** : pas de dépendance à un cloud, fonctionne hors ligne
- **Abordable** : pas d'abonnement, pas d'API payante

Cas d'usage concrets :
- Étudiant analysant ses cours sans exposer ses données
- Professionnel de santé travaillant sur des dossiers confidentiels
- Journaliste protégeant ses sources
- Utilisateur dans une zone sans internet fiable

---

## Lien de démo vidéo

> 📹 **[Lien YouTube à ajouter]**

---

## Repo GitHub

> 🔗 https://github.com/Smart-Learn-Squad/bissi

---

## Équipe

- **Tobie Amadou** — Design & Frontend (Electron, UI/UX)
- **Samuel** — Backend & Architecture (FastAPI, agent, llama.cpp)

---

## Checklist soumission

- [ ] Repo public sur GitHub
- [ ] Vidéo démo YouTube (max 3 min)
- [ ] Rapport Kaggle soumis
- [ ] PR `bissi/design` mergée dans `main`
- [ ] README à jour
