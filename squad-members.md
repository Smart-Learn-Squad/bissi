# 🤖 BISSI Squad — Guide pour les membres

Bienvenue dans l'équipe BISSI ! Ce guide t'explique comment installer et contribuer au projet, même si tu n'es pas expert en informatique.

---

## 🚀 INSTALLATION (Super simple !)

### Pour Windows :
1. Ouvre **PowerShell** (cherche "PowerShell" dans le menu Démarrer)
2. Copie-colle cette commande et appuie sur Entrée :
   ```powershell
   iwr -useb https://raw.githubusercontent.com/Smart-Learn-Squad/bissi/main/install.bat | cmd
   ```

### Pour Mac/Linux :
1. Ovre le **Terminal** 
2. Copie-colle cette commande et appuie sur Entrée :
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Smart-Learn-Squad/bissi/main/install.sh | sh
   ```

**Ce que l'installation fait automatiquement :**
- ✅ Vérifie que tu as les outils nécessaires
- ✅ Télécharge le projet
- ✅ Installe les dépendances
- ✅ Télécharge le modèle IA (3 GB - prévois du temps !)
- ✅ Ouvre VS Code
- ✅ Lance BISSI

---

## 👥 QUI FAIT QUOI

### 🎨 Équipe DESIGN (Interface visuelle)
**Tu peux modifier :**
- `bissi-master-ui/renderer/chat.html` → L'interface de chat
- `bissi-master-ui/renderer/onboarding.html` → La page d'accueil

**Ce que tu as le droit de changer :**
- Les couleurs (variables CSS en haut du fichier)
- Les espacements et la mise en page
- Les animations et transitions
- Les tailles de police

**Variables CSS importantes :**
```css
--acc: #7C3AED;    /* Couleur principale (violet) */
--bg: #0D0D12;     /* Fond de l'écran (sombre) */
--sb: #1A1A2E;     /* Barre latérale */
--text: #E2E8F0;   /* Texte principal */
```

**⛔ CE QU'IL NE FAUT PAS TOUCHER :**
- Les fonctions JavaScript (tout ce qui commence par `function`)
- Les `id` et `class` utilisées par le code
- La structure des boutons et éléments interactifs

---

### 🔧 Équipe BACKEND (Cerveau de BISSI)
**Seuls les experts peuvent modifier :**
- `core/` — Le moteur de l'IA
- `api/` — La communication entre l'interface et l'IA
- `functions/` — Les outils de BISSI
- `main.py` — Le démarrage du programme

---

## 📝 COMMENT CONTRIBUTION (Simple !)

### 1. Faire une modification
```bash
# Créer ta branche (ton espace de travail personnel)
git checkout -b design/ce-que-tu-modifies

# Modifier les fichiers autorisés seulement
# Teste en lançant : npm start
```

### 2. Proposer tes changements
```bash
# Ajouter tes modifications
git add .

# Envoyer sur GitHub
git commit -m "design: change la couleur des boutons en bleu"
git push origin design/ce-que-tu-modifies
```

### 3. Faire une Pull Request
1. Va sur GitHub
2. Clique sur "Compare & pull request"
3. Décrit ce que tu as changé
4. **IMPORTANT** : Demande un review à l'équipe concernée

---

## 🔴 RÈGLES DE SÉCURITÉ

### Pour l'équipe DESIGN :
- ✅ Tu peux modifier l'apparence visuelle
- ✅ Tu peux changer les couleurs, polices, espacements
- ❌ **JAMAIS** toucher au JavaScript
- ❌ **JAMAIS** modifier les `id` et `class`
- ❌ **JAMAIS** changer la structure des boutons

### Pour tout le monde :
- 🚨 Si tu as un doute : **NE TOUCHE À RIEN**
- 💬 Ouvre une "Issue" sur GitHub et pose ta question
- 👨‍💻 Sam (@goldensam777) valide tous les changements backend

---

## 🆘 EN CAS DE PROBLÈME

### L'installation ne marche pas ?
1. Vérifie que tu as bien copié toute la commande
2. Assure-toi d'avoir une connexion internet
3. Sur Windows : essaie d'exécuter PowerShell en tant qu'administrateur

### Tu ne sais pas si tu as le droit de modifier un fichier ?
1. Regarde la section "QUI FAIT QUOI" ci-dessus
2. Si le fichier n'est pas dans ta liste : **NE TOUCHE PAS**
3. Demande sur le Discord ou ouvre une Issue GitHub

### Tu as cassé quelque chose ?
1. **PANIQUE PAS** 🤗
2. Annule tes changements : `git checkout -- le-fichier-que-t-as-modifie`
3. Si ça ne marche pas : `git reset --hard HEAD`
4. Demande de l'aide !

---

## 📞 CONTACTS

- **Sam** (@goldensam777) — Responsable backend, il valide tout ce qui est technique
- **Équipe design** — Libre sur l'interface visuelle
- **Discord** — Pour les questions rapides
- **GitHub Issues** — Pour les problèmes et suggestions

---

## 🎉 BON À SAVOIR

- BISSI fonctionne 100% sur ton ordinateur (aucune donnée ne part sur internet)
- Le modèle IA fait 3 GB (prévois du temps pour le téléchargement)
- Tu peux personnaliser l'interface comme tu veux (dans les limites autorisées)
- Toute contribution est appréciée, même petite !

**Bienvenue dans l'aventure BISSI ! 🚀**
