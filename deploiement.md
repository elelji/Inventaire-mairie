# Étapes restantes — Déploiement de l'application

## Situation actuelle ✅

* [x] Application FastAPI fonctionnelle
* [x] Code nettoyé
* [x] `.gitignore` configuré
* [x] Données sensibles exclues (`.env`, base de données, fichiers Excel)
* [x] Projet envoyé sur le Git du Garage Numérique

---

# Étape 1 — Préparer le projet pour le déploiement

## Vérifications

Avant de continuer :

```bash
git status
```

Objectif :

```
nothing to commit, working tree clean
```

Vérifier que le projet contient :

```
projet_mairie/
│
├── app/
├── requirements.txt
├── README.md
├── .gitignore
└── Dockerfile
```

---

# Étape 2 — Créer le Dockerfile

Objectif :

Créer une image contenant :

* Python
* les dépendances
* le code de l'application
* la commande de démarrage

Structure :

```
Code source
      |
      ↓
Dockerfile
      |
      ↓
Image Docker
      |
      ↓
Conteneur
```

Commande de création :

```bash
touch Dockerfile
```

---

# Étape 3 — Tester l'application dans Docker

Construire l'image :

```bash
docker build -t projet-mairie .
```

Vérifier l'image :

```bash
docker images
```

Lancer le conteneur :

```bash
docker run -p 8000:8000 projet-mairie
```

Tester :

```
http://localhost:8000
```

ou :

```
http://localhost:8000/docs
```

Objectif :

L'application doit fonctionner exactement comme en local.

---

# Étape 4 — Ajouter la configuration

Ne jamais mettre les secrets dans Git.

Utiliser :

```
.env
```

Exemple :

```
DATABASE_URL=
SECRET_KEY=
```

Créer un modèle partageable :

```
.env.example
```

Exemple :

```
DATABASE_URL=mettre_la_valeur
SECRET_KEY=changer_la_valeur
```

---

# Étape 5 — Préparer le déploiement sur un serveur

Questions à poser au tuteur / service informatique :

## Où installer l'application ?

* Serveur physique ?
* Machine virtuelle ?
* Serveur interne ?

## Qui doit y accéder ?

* Une personne ?
* Une école ?
* Toutes les écoles ?
* Service informatique uniquement ?

## Informations réseau nécessaires :

* Adresse IP du serveur
* Port utilisé
* Règles firewall
* Accès réseau

---

# Étape 6 — Comprendre l'accès réseau

Localement :

```
localhost:8000
```

Seulement mon ordinateur.

Sur un réseau :

```
IP_SERVEUR:8000
```

Exemple :

```
192.168.1.50:8000
```

Le serveur doit :

* écouter sur le réseau
* autoriser le port
* être accessible depuis les postes utilisateurs

---

# Étape 7 — Déployer une première version de test

Workflow :

```
Modification du code
        |
        ↓
git commit
        |
        ↓
docker build
        |
        ↓
nouvelle image Docker
        |
        ↓
serveur de test
        |
        ↓
validation par le tuteur
```

Versionner les images :

```
projet-mairie:v1
projet-mairie:v2
projet-mairie:v3
```

---

# Étape 8 — Mise en production (plus tard)

Architecture cible possible :

```
Utilisateur
     |
     |
Réseau mairie
     |
     |
Serveur Linux
     |
     |
Docker
     |
     ├── FastAPI
     |
     └── Base de données
```

Améliorations possibles :

* Nginx (serveur web)
* HTTPS
* sauvegardes
* gestion des utilisateurs
* logs

---

# Objectif de la prochaine démonstration

À montrer au tuteur :

✅ Code disponible sur Git
✅ README présent
✅ Application fonctionnelle
✅ Application lancée dans Docker
✅ Explication du futur déploiement réseau

---

# Commandes utiles

Voir l'état Git :

```bash
git status
```

Envoyer les modifications :

```bash
git add .
git commit -m "message"
git push
```

Créer une image Docker :

```bash
docker build -t projet-mairie .
```

Lancer un conteneur :

```bash
docker run -p 8000:8000 projet-mairie
```

Voir les conteneurs :

```bash
docker ps
```

Arrêter un conteneur :

```bash
docker stop nom_du_conteneur
```
