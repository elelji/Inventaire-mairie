# Inventaire DSI — Guide de passation

Application d'inventaire informatique pour la DSI de la mairie.

## 1. Démarrer / Arrêter l'application

**Démarrer :**
Double-cliquer sur le raccourci `Demarrer_Inventaire.bat` sur le bureau.
Une fenêtre s'ouvre et affiche les logs — attendre le message `Application startup complete`. Le navigateur s'ouvre automatiquement après quelques secondes sur la page de connexion.

**Arrêter :**
Fermer simplement la fenêtre qui s'est ouverte (la croix). L'application s'arrête proprement.


## 2. Accéder à l'application depuis un autre poste

Depuis le PC qui héberge l'application : `http://localhost`

Depuis un autre poste du réseau : `http://192.168.16.1`

## 3. Sauvegarder la base de données

Toutes les données sont stockées dans un seul fichier :
Stage/app/database.db

**Recommandation :** copier ce fichier régulièrement (ex: une fois par semaine) vers un autre emplacement (clé USB, dossier partagé) pour éviter toute perte de données en cas de problème sur le PC.

Exemple de commande de sauvegarde (à adapter) :
copy app\database.db D:\Sauvegardes\database_JJMMAAAA.db
---

## 4. Fichier de configuration sensible (.env)

Le fichier `.env` à la racine du projet contient des informations sensibles :
- `SESSION_SECRET_KEY` : clé secrète de session
- `EMAIL_DSI` / `EMAIL_DSI_MOT_DE_PASSE` : identifiants d'envoi d'email (2FA)
- `AGENT_API_KEY` : clé API pour l'agent de récupération réseau
- `APP_BASE_URL` (optionnel) : URL publique de l'application, utilisée dans les emails de réinitialisation de mot de passe (défaut : `http://localhost:8000`)

**Ne jamais partager ce fichier ni le rendre accessible publiquement, et ne jamais committer une vraie clé dans le code source.**

`script.ps1` (déployé sur les postes) contient un placeholder `REMPLACER_PAR_LA_CLE_API_AGENT` pour `$apiKey` : la vraie valeur ne doit être renseignée que sur les copies déployées localement sur chaque poste, jamais dans le dépôt git.

Si `AGENT_API_KEY` doit être régénérée, il faut la mettre à jour à la fois dans `.env` et dans `$apiKey` sur chaque copie de `script.ps1` déployée sur les postes.

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