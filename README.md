# 🤖 BISSI — Votre assistant IA local et privé

**BISSI** est un assistant IA personnel qui fonctionne 100% sur votre machine, sans aucune connexion internet. Basé sur Gemma 4, il vous aide dans vos tâches quotidiennes tout en protégeant votre vie privée.

---

## 🚀 Installation (One-liner)

### Windows
```powershell
iwr -useb https://raw.githubusercontent.com/Smart-Learn-Squad/bissi/main/install.bat -OutFile install.bat; .\install.bat
```

### Mac/Linux
```bash
curl -fsSL https://raw.githubusercontent.com/Smart-Learn-Squad/bissi/main/install.sh | bash
```

**L'installation automatique inclut :**
- ✅ Dépendances Python et Node.js
- ✅ Téléchargement du modèle IA (~3 GB)
- ✅ Configuration de l'environnement
- ✅ Lancement automatique

---

## 🏆 Fonctionnalités

### 🎯 Assistant Intelligent
- **Conversation naturelle** en français et anglais
- **Mémoire persistante** de vos discussions
- **Contexte automatique** de vos fichiers et projets
- **Adaptation** à votre style et préférences

### 🛠️ Outils Intégrés
- **📁 Gestion de fichiers** : lire, écrire, organiser
- **💻 Programmation** : Python, analyse de code, debugging
- **📊 Bureautique** : Word, Excel, PowerPoint, PDF
- **🔍 Recherche** : navigation web, analyse de contenu
- **📈 Données** : CSV, analyse, graphiques
- **🖼️ Vision** : images, screenshots, OCR
- **📋 Presse-papiers** : copier/coller intelligent

### 🔒 Confidentialité
- **100% local** : aucune donnée ne quitte votre machine
- **Pas de tracking** : votre vie privée est respectée
- **Chiffrement** : vos conversations sont protégées

---

## 🏗️ Architecture

### Backend Python
```
core/                    # Moteur de l'agent
├── agent.py            # Orchestrateur principal
├── engine.py           # Interface avec le modèle
├── memory/             # Mémoire conversationnelle
└── context.py          # Gestion du contexte

functions/              # Outils de l'agent
├── filesystem/        # Gestion de fichiers
├── code/              # Programmation
├── office/            # Bureautique
├── data/              # Analyse de données
└── vision/            # Traitement d'images

api/server.py          # API FastAPI
main.py               # Point d'entrée
```

### Frontend Electron
```
bissi-master-ui/
├── main.js            # Processus principal
├── preload.js         # Bridge sécurisé
└── renderer/          # Interface utilisateur
    ├── chat.html      # Chat principal
    └── onboarding.html # Page d'accueil
```

---

## 💻 Utilisation

### Démarrage Rapide
```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

### Développement
```bash
# Backend
python main.py

# Frontend
cd bissi-master-ui
npm start
```

### API Directe
```bash
# Santé du serveur
curl http://localhost:8765/health

# Chat (Streaming)
curl -N -X POST "http://localhost:8765/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"Bonjour BISSI","conversation_id":null}'
```

---

## 🛠️ Configuration

### Modèle IA
- **Modèle** : `unsloth/gemma-4-E2B-it-GGUF`
- **Quantification** : Q4_K_M (optimisée pour CPU)
- **Contexte** : 4096 tokens
- **Taille** : ~3 GB

### Personnalisation
```python
# configs/personas/office_assistant.py
# configs/personas/student.py
# configs/personas/researcher.py
```

---

## 📚 Documentation

- **[squad-members.md](./squad-members.md)** — Guide pour les contributeurs
- **[AGENTS.md](./AGENTS.md)** — Règles de contribution
- **[install.sh](./install.sh)** — Script d'installation Linux/Mac
- **[install.bat](./install.bat)** — Script d'installation Windows

---

## 🤝 Contribution

### Équipes
- **🎨 Design** : Interface utilisateur, CSS, animations
- **🔧 Backend** : Moteur IA, API, outils

### Workflow
1. Forker le repo
2. Créer une branche : `git checkout -b feature/nom-feature`
3. Faire les changements
4. Tester : `npm start` (frontend) ou `python main.py` (backend)
5. Pull Request avec review obligatoire

### Permissions
- Voir [AGENTS.md](./AGENTS.md) pour les règles détaillées
- Voir [.github/CODEOWNERS](./.github/CODEOWNERS) pour les approbations

---

## 🔧 Dépannage

### Problèmes Communs
- **Modèle introuvable** : Vérifiez le téléchargement HF
- **Port occupé** : Changez les ports dans la config
- **Mémoire insuffisante** : Réduisez `n_ctx` dans la config

### Logs
- **Backend** : `~/.bissi/logs/`
- **Frontend** : Console développeur Electron
- **Système** : `/tmp/bissi-*.log` (Linux) ou `%TEMP%\bissi-*.log` (Windows)

---

## 📊 Stack Technique

### Backend
- **Python 3.11+** avec FastAPI
- **llama-cpp-python** pour le modèle
- **SQLite** pour les conversations
- **ChromaDB** pour la mémoire vectorielle
- **Pydantic** pour la validation

### Frontend
- **Electron** pour l'application desktop
- **HTML/CSS/JS** natifs
- **PDF.js**, **xlsx**, **mammoth** pour les documents

### Modèle
- **Gemma 4** (Google)
- **GGUF** pour l'optimisation CPU
- **Quantifié** Q4_K_M pour l'équilibre performance/taille

---

## 📄 Licence

MIT License — Voir [LICENSE](./LICENSE) pour plus d'informations.

---

## 🙏 Remerciements

- **Google** pour le modèle Gemma 4
- **Hugging Face** pour l'hébergement des modèles
- **Ollama** pour l'inférence locale
- **Équipe Gemma 4 Good** pour le hackathon

---

**BISSI** — Votre assistant IA, privé et performant. 🚀
