# Inventaire DSI

Application web de gestion de l'inventaire informatique, développée en stage pour la DSI de la mairie de Gonesse.

## Contexte

Le parc informatique était suivi dans des fichiers Excel dispersés : doublons, recherche difficile, suivi du matériel compliqué. L'application centralise ces données dans une base unique, accessible depuis le réseau et sécurisée par rôles.

## Fonctionnalités

- **Gestion du parc** : équipements, lieux, consommables, corbeille
- **Recherche avancée** et filtres dynamiques
- **Import** des données Excel existantes (nettoyage et uniformisation automatiques vers la base)
- **Export** Excel et PDF des équipements encore dans le parc, ainsi que des équipements supprimés du parc.
- **Garanties** : récupération automatique des informations de garantie (Epson)
- **Collecte automatique du matériel** : script PowerShell déployé sur les postes, qui envoie les informations à l'API de l'application (authentifiée par clé API)
- **Sécurité** : authentification à deux facteurs (TOTP, compatible Google Authenticator), rôles et permissions avec interface d'administration, réinitialisation de mot de passe par e-mail
- **Exploitation** : lancement en un clic sous Windows et Linux (installation de Docker si absent, vérification de la configuration, création de la base au premier démarrage), sauvegarde automatique de la base vers un emplacement configurable, journalisation des connexions et des erreurs.
  
## Stack technique

| Couche | Technologies |
|---|---|
| Backend | Python, FastAPI, SQLModel |
| Base de données | SQLite |
| Frontend | Jinja2 (rendu côté serveur), Bootstrap |
| Déploiement | Docker, docker-compose, nginx (reverse proxy) |
| Automatisation | PowerShell, Python |

## Captures d'écran

<img width="1920" height="1080" alt="capture-dashboard" src="https://github.com/user-attachments/assets/51c25b4e-e7e6-40d6-950b-ece9e43e04bc" />
<img width="1920" height="877" alt="capture-utilisateurs" src="https://github.com/user-attachments/assets/f169ce74-7aba-44d8-92bb-72a5128392c3" />
<img width="1920" height="853" alt="capture-export" src="https://github.com/user-attachments/assets/ad53222b-4087-4440-a92b-e2ef52cf3d05" />

## Installation

Prérequis : Docker et Docker Compose.

1. Cloner le dépôt puis créer le fichier de configuration :
   ```bash
   cp .env.example .env
   ```
   Renseigner ensuite les valeurs dans `.env` (clé de session, identifiants d'envoi d'e-mails, clé API de l'agent).

2. Lancer l'application :
   ```bash
   docker compose up
   ```

3. Dans un second terminal, initialiser les permissions et créer le premier compte administrateur :
   ```bash
   docker compose exec app python scripts/seed_permissions.py
   docker compose exec app python scripts/create_admin.py
   ```

4. Ouvrir `http://localhost`.

Alternative plus simple : « Lancer deployment/Inventaire_d.bat » pour Windows ou Inventaire_d.sh pour Linux.

## Architecture

```
app/            Application FastAPI (routes, modèles, authentification, templates, utilitaires)
scripts/        Scripts d'administration (création de l'admin, import Excel, données initiales)
deployment/     Configuration nginx, lanceurs, script de collecte et de sauvegarde
```

Deux services Docker : `app` (FastAPI) et `nginx` (reverse proxy).

## Choix techniques

- **2FA par TOTP** : standard ouvert, fonctionne avec toute application d'authentification.
- **Rôles et permissions** : chaque utilisateur n'accède qu'aux fonctions dont il a besoin.
- **Secrets hors du dépôt** : clés et identifiants dans un fichier `.env` non versionné, clé API de l'agent à renseigner uniquement sur les copies déployées.
- **Conteneurisation** : déploiement reproductible, sans installer Python sur le poste hôte.
- **Rendu côté serveur** : l'utilisation de Jinja2 permet un rendu serveur simple à maintenir sans partie frontend séparée.
- **Fichiers de lancements**: un lanceur qui vérifie les prérequis évite les erreurs d’exploitation pour des agents qui ne connaissent pas Docker.
  
## Documentation d'exploitation

Voir le [guide de passation](docs/PASSATION.md) : démarrage, sauvegarde, configuration, logs.

## Auteure

Emma L. : [LinkedIn](https://www.linkedin.com/in/emma-louisy-louis-joseph/)
