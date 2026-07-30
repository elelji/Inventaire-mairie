@echo off
cd /d C:\chemin\vers\ton\projet
start /min cmd /c "timeout /t 15 && start http://localhost"
docker compose up