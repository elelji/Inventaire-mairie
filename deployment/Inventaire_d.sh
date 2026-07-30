#!/bin/bash
# Lance l'application Inventaire DSI via Docker Compose (Linux).
# Installe Docker automatiquement si besoin.
set -e

# Se place à la racine du projet, peu importe d'où le script est appelé
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé sur ce poste. Installation en cours..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    rm -f /tmp/get-docker.sh
fi

if ! docker compose version &> /dev/null; then
    echo "Le plugin 'docker compose' est manquant. Installation en cours..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

if ! sudo docker info &> /dev/null; then
    echo "Le service Docker ne semble pas démarré, tentative de démarrage..."
    sudo systemctl start docker
fi

(sleep 15 && xdg-open http://localhost) &
sudo docker compose up
