# Inventaire DSI — Guide de passation

Application d'inventaire informatique pour la DSI de la mairie.

## 1. Démarrer / Arrêter l'application

**Démarrer :**
Double-cliquer sur le raccourci bureau qui pointe vers `deployment/Inventaire_d.bat`.
Une fenêtre s'ouvre et affiche les logs — attendre le message `Application startup complete`. Le navigateur s'ouvre automatiquement après quelques secondes sur la page de connexion.

> Le raccourci bureau doit pointer vers le fichier `deployment/Inventaire_d.bat` du projet (et non plus vers un `.bat` à la racine). Pense à corriger le raccourci existant si besoin.

**Arrêter :**
Fermer simplement la fenêtre qui s'est ouverte (la croix). L'application s'arrête proprement.


## 2. Accéder à l'application depuis un autre poste

Depuis le PC qui héberge l'application : `http://localhost`

Depuis un autre poste du réseau : `http://192.168.16.1`

## 3. Sauvegarder la base de données

Toutes les données sont stockées dans un seul fichier :
`app/database.db`

**Recommandation :** copier ce fichier régulièrement (ex: une fois par semaine) vers un autre emplacement (clé USB, dossier partagé) pour éviter toute perte de données en cas de problème sur le PC. Le script `deployment/sauvegarde_inventaire.ps1` automatise cette copie (à planifier via le planificateur de tâches Windows).

Exemple de commande de sauvegarde manuelle (à adapter) :
copy app\database.db D:\Sauvegardes\database_JJMMAAAA.db
---

## 4. Fichier de configuration sensible (.env)

Le fichier `.env` à la racine du projet contient des informations sensibles et n'est **jamais** commité dans git. Avant le tout premier lancement sur un poste, le créer à partir du modèle fourni :

```
copy .env.example .env      (Windows)
cp .env.example .env         (Linux)
```

puis remplir les vraies valeurs :
- `SESSION_SECRET_KEY` : clé secrète de session (chaîne aléatoire longue)
- `EMAIL_DSI` / `EMAIL_DSI_MOT_DE_PASSE` : identifiants d'envoi d'email (2FA, mot de passe oublié, création de compte)
- `AGENT_API_KEY` : clé API pour l'agent de récupération réseau
- `APP_BASE_URL` (optionnel) : URL publique de l'application, utilisée dans les emails de réinitialisation de mot de passe (défaut : `http://localhost:8000`)

Sans ce fichier, l'application ne démarre pas (les scripts `deployment/Inventaire_d.bat`/`.sh` vérifient sa présence et arrêtent proprement sinon).

**Ne jamais partager ce fichier ni le rendre accessible publiquement, et ne jamais committer une vraie clé dans le code source.**

`deployment/script.ps1` (déployé sur les postes) contient un placeholder `REMPLACER_PAR_LA_CLE_API_AGENT` pour `$apiKey` : la vraie valeur ne doit être renseignée que sur les copies déployées localement sur chaque poste, jamais dans le dépôt git.

Si `AGENT_API_KEY` doit être régénérée, il faut la mettre à jour à la fois dans `.env` et dans `$apiKey` sur chaque copie de `deployment/script.ps1` déployée sur les postes.

## 4bis. Premier démarrage : créer le compte administrateur

La base de données est vide au premier lancement (aucun utilisateur, aucune permission). Une fois l'application démarrée (`docker compose up`, voir section 1), ouvrir un **second** terminal depuis la racine du projet et exécuter, dans l'ordre :

```
docker compose exec app python scripts/seed_permissions.py
docker compose exec app python scripts/create_admin.py
```

`create_admin.py` demande un email et un mot de passe et crée le premier compte administrateur. Ces commandes s'exécutent **dans le conteneur** (`docker compose exec`), pas directement sur le poste — pas besoin d'installer Python ni les dépendances sur la machine hôte.

## 5. Consulter les logs en cas de problème

Dans un terminal, depuis le dossier du projet :
docker compose logs

Pour voir les logs en direct pendant que l'app tourne :
docker compose logs -f

## 6. En cas de bug bloquant

- Vérifier d'abord les logs (section 5) pour identifier l'erreur
- [À compléter : contact de la personne à joindre, ou procédure de remontée à la DSI]

## Structure technique (pour référence)

- **Backend** : FastAPI + SQLModel + SQLite
- **Frontend** : Jinja2 (rendu côté serveur) + Bootstrap
- **Déploiement** : Docker + docker-compose (2 services : `app` + `nginx` en reverse proxy)
- **Port exposé** : 80 (HTTP)

## Organisation du dépôt

```
app/                  Code de l'application (package Python)
  main.py             Point d'entrée FastAPI
  models.py           Modèles SQLModel (tables de la base)
  auth.py             Authentification, 2FA, envoi d'emails
  dependencies.py     Session DB, logger, moteur SQL, templates Jinja2
  routes/             Routes HTTP, une fichier par domaine métier
  templates/          Templates Jinja2 (HTML)
  utils/              Fonctions utilitaires réutilisées par l'app (scrapers
                       de garantie, calculs consommables, import Excel)
scripts/              Scripts d'administration à lancer manuellement, une
                       fois, depuis la racine du projet — en local avec un
                       venv : `python scripts/create_admin.py` ; via Docker :
                       `docker compose exec app python scripts/create_admin.py`
                       (voir section 4bis)
deployment/           Fichiers de déploiement/exploitation : lanceurs
                       desktop, config nginx, scripts d'agent réseau et de
                       sauvegarde
Dockerfile, docker-compose.yml   Build et orchestration Docker
requirements.txt      Dépendances Python
```