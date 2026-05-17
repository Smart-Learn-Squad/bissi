@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo Bienvenue dans l'installateur de Bissi 🤖
echo Voici ce qui va se passer :
echo 1. Vérification des outils requis
echo 2. Clonage du repo GitHub
echo 3. Création du virtualenv Python
echo 4. Installation de huggingface-cli
echo 5. Installation des dépendances npm
echo 6. Téléchargement du modèle IA ^(~3 GB^)
echo 7. Ouverture de VS Code
echo 8. Lancement de l'application
echo.

REM ÉTAPE 1 — Vérifications
echo → Vérification des outils requis...

for %%T in (git node npm python curl) do (
    where %%T >nul 2>&1
    if errorlevel 1 (
        echo ❌ %%T n'est pas installé. Installe-le puis relance ce script.
        exit /b 1
    ) else (
        echo ✓ %%T trouvé
    )
)

REM ÉTAPE 2 — Clone du repo
if defined BISSI_INSTALL_DIR (
    set "PROJECT_DIR=%BISSI_INSTALL_DIR%"
) else (
    set "PROJECT_DIR=%USERPROFILE%\Documents\Projets\Bissi"
)
if not exist "%PROJECT_DIR%" mkdir "%PROJECT_DIR%"
cd /d "%PROJECT_DIR%"

set "WRITE_TEST_FILE=%PROJECT_DIR%\.__bissi_write_test__"
echo test>"%WRITE_TEST_FILE%" 2>nul
if not exist "%WRITE_TEST_FILE%" (
    echo ❌ Dossier d'installation non inscriptible: %PROJECT_DIR%
    echo → Définit un dossier writable: set BISSI_INSTALL_DIR=%%USERPROFILE%%\Documents\Projets\Bissi
    exit /b 1
)
del "%WRITE_TEST_FILE%" >nul 2>&1

set "REPO_URL=https://github.com/Smart-Learn-Squad/bissi.git"
if exist "bissi" (
    echo ⚠ Le repo existe déjà. On continue quand même.
    cd bissi
    git pull --ff-only
    if errorlevel 1 (
        echo ⚠ Impossible de mettre à jour automatiquement le repo ^(conflit ou historique local^).
        echo   On continue avec l'état local actuel.
    )
) else (
    echo → Clonage du repo...
    git clone "%REPO_URL%"
    if errorlevel 1 (
        echo ❌ Échec du clonage du repo
        exit /b 1
    )
    echo ✓ Repo cloné avec succès
    cd bissi
)

REM ÉTAPE 3 — Virtualenv Python
echo → Création du virtualenv Python...
if exist ".venv" (
    echo ⚠ .venv existe déjà. On réutilise.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Échec de la création du virtualenv
        exit /b 1
    )
    echo ✓ .venv créé
)

call .venv\Scripts\activate.bat
echo ✓ Virtualenv activé

REM ÉTAPE 4 — Mise à jour pip + dépendances Python
echo → Mise à jour de pip...
python -m pip install --upgrade pip -q
if errorlevel 1 (
    echo ❌ Échec de la mise à jour de pip
    exit /b 1
)
echo ✓ pip mis à jour

echo → Installation des dépendances Python...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Échec de l'installation des dépendances Python
    exit /b 1
)
echo ✓ Dépendances Python installées

echo → Installation de huggingface-cli...
python -m pip install --upgrade huggingface_hub -q
if errorlevel 1 (
    echo ❌ Échec de l'installation de huggingface-hub
    exit /b 1
)
echo ✓ huggingface-cli installé

REM ÉTAPE 5 — npm install
echo → Installation des dépendances npm...
cd bissi-master-ui
npm install
if errorlevel 1 (
    echo ❌ Échec de l'installation npm
    exit /b 1
)
echo ✓ Dépendances npm installées
cd ..

REM ÉTAPE 6 — Téléchargement modèle
echo.
echo → Téléchargement du modèle IA ^(~3 GB^)...
echo   Cela peut prendre plusieurs minutes selon votre connexion.
echo   Ne fermez pas ce terminal.
echo.

if not exist "models" mkdir models
if exist "models\gemma-4-E2B-it-Q4_K_M.gguf" (
    echo ✓ Modèle déjà présent dans .\models\
) else (
    set "HF_CLI=hf"
    where !HF_CLI! >nul 2>&1
    if errorlevel 1 (
        set "HF_CLI=huggingface-cli"
        where !HF_CLI! >nul 2>&1
        if errorlevel 1 (
            set "HF_CLI=python -m huggingface_hub.commands.huggingface_cli"
        )
    )

    !HF_CLI! download unsloth/gemma-4-E2B-it-GGUF gemma-4-E2B-it-Q4_K_M.gguf --local-dir ./models --local-dir-use-symlinks False
    if errorlevel 1 (
        echo ❌ Échec du téléchargement du modèle
        exit /b 1
    )
    echo ✓ Modèle téléchargé dans ./models/
)

REM ÉTAPE 7 — Ouverture VS Code
echo.
echo → Ouverture de VS Code...
where code >nul 2>&1
if !errorlevel! equ 0 (
    code .
) else (
    echo ⚠ VS Code non trouvé. Ouvre le dossier manuellement.
)

REM ÉTAPE 8 — Lancement
echo.
echo → Lancement de Bissi...
call start.bat
if errorlevel 1 exit /b 1
