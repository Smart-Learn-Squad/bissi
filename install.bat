@echo off
chcp 65001 >nul

echo Bienvenue dans l'installateur de Bissi 🤖
echo Voici ce qui va se passer :
echo 1. Vérification des outils requis
echo 2. Installation de huggingface-cli si absent
echo 3. Création du dossier projet
echo 4. Clonage du repo GitHub
echo 5. Installation des dépendances npm
echo 6. Téléchargement du modèle IA ^(~3 GB^)
echo 7. Ouverture de VS Code
echo 8. Lancement de l'application
echo.

REM ÉTAPE 1 — Vérifications
echo → Vérification des outils requis...

:check_tool
if not "%1"=="" (
    where %1 >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ %1 n'est pas installé.
        echo → Installe-le depuis %2 puis relance ce script.
        exit /b 1
    ) else (
        echo ✓ %1 trouvé
    )
)

call :check_tool git https://git-scm.com
call :check_tool node https://nodejs.org
call :check_tool npm https://nodejs.org
call :check_tool python https://python.org
call :check_tool pip https://python.org
call :check_tool curl https://curl.se

REM ÉTAPE 2 — huggingface-cli
where huggingface-cli >nul 2>&1
if %errorlevel% neq 0 (
    echo → Installation de huggingface-cli...
    pip install huggingface-hub -q
    echo ✓ huggingface-cli installé
) else (
    echo ✓ huggingface-cli déjà installé
)

REM ÉTAPE 3 — Dossier projet
set "PROJECT_DIR=%USERPROFILE%\Documents\Projets\Bissi"
if exist "%PROJECT_DIR%" (
    echo ⚠ Le dossier existe déjà. On continue quand même.
) else (
    echo → Création du dossier %PROJECT_DIR%...
    mkdir "%PROJECT_DIR%"
    echo ✓ Dossier créé
)

cd /d "%PROJECT_DIR%"

REM ÉTAPE 4 — Clone du repo
set "REPO_URL=https://github.com/Smart-Learn-Squad/bissi.git"
if exist "bissi" (
    echo ⚠ Le repo existe déjà. On continue quand même.
    cd bissi
) else (
    echo → Clonage du repo...
    git clone "%REPO_URL%"
    if %errorlevel% neq 0 (
        echo ❌ Échec du clonage du repo
        exit /b 1
    )
    echo ✓ Repo cloné avec succès
    cd bissi
)

REM ÉTAPE 5 — npm install
echo → Installation des dépendances npm...
cd bissi-master-ui
npm install
if %errorlevel% neq 0 (
    echo ❌ Échec de l'installation npm
    exit /b 1
)
echo ✓ Dépendances npm installées

REM ÉTAPE 6 — Téléchargement modèle
echo.
echo → Téléchargement du modèle IA ^(~3 GB^)...
echo   Cela peut prendre plusieurs minutes selon votre connexion.
echo   Ne fermez pas ce terminal.
echo.

cd ..
mkdir models 2>nul
huggingface-cli download unsloth/gemma-4-E2B-it-GGUF gemma-4-E2B-it-Q4_K_M.gguf --local-dir ./models --local-dir-use-symlinks False
if %errorlevel% neq 0 (
    echo ❌ Échec du téléchargement du modèle
    exit /b 1
)
echo ✓ Modèle téléchargé dans ./models/

REM ÉTAPE 7 — Ouverture VS Code
echo.
echo → Ouverture de VS Code...
echo   VS Code va s'ouvrir sur le projet.
echo   Ne fermez pas ce terminal, l'application va démarrer.

where code >nul 2>&1
if %errorlevel% equ 0 (
    code .
) else (
    echo ⚠ VS Code non trouvé. Ouvre le dossier manuellement.
)

REM ÉTAPE 8 — Lancement
echo.
echo → Lancement de Bissi...
call start.bat
