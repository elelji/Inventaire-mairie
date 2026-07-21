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

Depuis un autre poste du réseau : `http://[IP_A_COMPLETER]`
*(à compléter une fois l'adresse IP fixe du PC hôte connue — demander à la DSI si besoin de la fixer)*

## 3. Sauvegarder la base de données

Toutes les données sont stockées dans un seul fichier :
[chemin_du_projet]/app/database.db

**Recommandation :** copier ce fichier régulièrement (ex: une fois par semaine) vers un autre emplacement (clé USB, dossier partagé) pour éviter toute perte de données en cas de problème sur le PC.

Exemple de commande de sauvegarde (à adapter) :
copy app\database.db D:\Sauvegardes\database_JJMMAAAA.db
---

## 4. Fichier de configuration sensible (.env)

Le fichier `.env` à la racine du projet contient des informations sensibles :
- Clé secrète de session
- Identifiants d'envoi d'email (2FA)
- Clé API pour l'agent de récupération réseau

**Ne jamais partager ce fichier ni le rendre accessible publiquement.**

Si une clé doit être régénérée (ex: la clé API agent), il faudra aussi la mettre à jour dans le script PowerShell déployé sur les postes.

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