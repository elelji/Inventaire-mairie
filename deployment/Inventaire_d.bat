@echo off
setlocal
REM Lance l'application Inventaire DSI via Docker Compose (Windows).
REM Installe Docker Desktop automatiquement si besoin (necessite winget).

REM Se place a la racine du projet, peu importe d'ou le script est appele
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker n'est pas installe sur ce poste.
    where winget >nul 2>nul
    if errorlevel 1 (
        echo Impossible d'installer Docker automatiquement ^(winget introuvable^).
        echo Installez Docker Desktop manuellement : https://www.docker.com/products/docker-desktop
        pause
        exit /b 1
    )
    echo Installation de Docker Desktop via winget, merci de patienter...
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    echo.
    echo Docker Desktop vient d'etre installe. Un redemarrage du PC est necessaire.
    echo Redemarrez le PC puis relancez ce raccourci.
    pause
    exit /b 0
)

docker info >nul 2>nul
if errorlevel 1 (
    echo Docker est installe mais ne semble pas demarre.
    echo Lancement de Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Attente du demarrage de Docker...
    timeout /t 30 /nobreak >nul
)

if not exist ".env" (
    echo ERREUR : le fichier .env est introuvable a la racine du projet.
    echo Cree-le avant de lancer l'application ^(voir le README, section 4^).
    pause
    exit /b 1
)

if not exist "app\database.db" (
    echo Premier lancement : creation du fichier de base de donnees vide...
    type nul > app\database.db
)

start /min cmd /c "timeout /t 15 && start http://localhost"
docker compose up
