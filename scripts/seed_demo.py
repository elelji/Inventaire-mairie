"""
Permet de générer une base de données de démonstration entièrement fictive car les données de mon stage sont cofidentielle.
Toutes les données et les comptes sont invisibles.

Usage (depuis la racine du projet) :
    python scripts/seed_demo.py            # refuse si la base contient déjà des équipements
    python scripts/seed_demo.py --reset    # VIDE la base puis la remplit avec la démo

Avec Docker :
    docker compose exec app python scripts/seed_demo.py --reset
"""
import sys
import os
import random
import argparse
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dateutil.relativedelta import relativedelta
from sqlmodel import SQLModel, Session, select

from app.dependencies import engine
from app.auth import hash_password
from app.models import (Equipement, Garantie, Consommable, Historique, User, Role, Permission, Lieu, LogConnexion)
from scripts.seed_permissions import PERMISSIONS_PAR_DEFAUT

# Paramètres de la démo
GRAINE = 2026
NB_EQUIPEMENTS = 150
MDP_DEMO = "Demo2026!"
# Secret TOTP public, volontairement publié dans le README pour la démo.
# À ne JAMAIS réutiliser sur une vraie instance.
TOTP_SECRET_DEMO = "DEMOINVENTAIREDSIDEMOINVENTAIRE2"

COMPTES_DEMO = [
    ("admin@demo.local", Role.administrateur),
    ("technicien@demo.local", Role.technicien),
    ("lecture@demo.local", Role.utilisateur),
]

# Permissions activées pour le rôle technicien dans la démo mais modulable au choix avec le profil administrateur directectement dans l'appli
PERMISSIONS_TECHNICIEN = {
    "ajouter_equipement", "modifier_equipement", "ajouter_categorie",
    "generer_pdf", "acces_corbeille", "consultation_sortie_inventaire",
    "remplacer_consommable", "creer_consommable", "voir_utilisateur",
}

LIEUX = [
    "Hôtel de Ville", "Centre technique municipal", "Médiathèque des Saules",
    "Conservatoire", "Police municipale", "CCAS", "Maison des associations",
    "École élémentaire Les Tilleuls", "École élémentaire Jean Moulin",
    "École maternelle Les Coquelicots", "École maternelle Le Petit Prince",
    "Groupe scolaire Pasteur", "Gymnase du Parc", "Centre de loisirs Arc-en-ciel",
]
SALLES = ["Accueil", "Bureau 1", "Bureau 2", "Bureau 3", "Salle de réunion",
          "Secrétariat", "Classe 1", "Classe 2", "Classe 3", "Salle informatique",
          "Local technique", "Direction", None]

SERVICES = ["Accueil", "État civil", "Urbanisme", "Ressources humaines",
            "Finances", "Services techniques", "Enfance", "Communication",
            "Direction générale", "Médiathèque", "Police municipale"]
PRENOMS = ["Camille", "Louis", "Inès", "Hugo", "Sarah", "Nathan", "Léa",
           "Yanis", "Chloé", "Mathis", "Jade", "Adam", "Manon", "Lucas"]
NOMS = ["Martin", "Bernard", "Petit", "Durand", "Leroy", "Moreau", "Simon",
        "Laurent", "Michel", "Garcia", "Roux", "Fournier", "Girard", "Mercier"]

# categorie: (poids, [(marque, [modèles], prix_min, prix_max)], os?)
CATALOGUE = {
    "PC fixe": (30, [("Dell", ["OptiPlex 7010", "OptiPlex 5000"], 650, 1100),
                     ("HP", ["EliteDesk 800 G6", "ProDesk 400 G9"], 600, 1000),
                     ("Lenovo", ["ThinkCentre M70q", "ThinkCentre M90s"], 620, 1050)], True),
    "PC portable": (20, [("Dell", ["Latitude 5440", "Latitude 7430"], 900, 1500),
                         ("HP", ["ProBook 450 G10", "EliteBook 840 G9"], 850, 1600),
                         ("Lenovo", ["ThinkPad E14", "ThinkPad T14"], 800, 1450)], True),
    "Écran": (25, [("Dell", ["P2422H", "P2723DE"], 150, 320),
                   ("Iiyama", ["ProLite XUB2493", "ProLite XU2793"], 130, 260),
                   ("HP", ["E24 G5", "E27 G5"], 160, 300)], False),
    "Imprimante": (10, [("Brother", ["HL-L6400DW", "MFC-L8900CDW"], 350, 900),
                        ("Kyocera", ["ECOSYS M3655idn", "TASKalfa 2554ci"], 700, 3500),
                        ("Canon", ["i-SENSYS MF655Cdw", "imageRUNNER C3326i"], 400, 3000)], False),
    "Vidéoprojecteur": (5, [("BenQ", ["MW560", "MH733"], 450, 900),
                            ("ViewSonic", ["PA503W", "LS610WH"], 400, 950)], False),
    "Tablette": (4, [("Samsung", ["Galaxy Tab A8", "Galaxy Tab S6 Lite"], 220, 400),
                     ("Apple", ["iPad 10e génération"], 420, 520)], False),
    "Switch": (3, [("Cisco", ["CBS250-24T", "C1000-24P"], 300, 1200),
                   ("HPE Aruba", ["Instant On 1930"], 250, 700)], False),
    "Borne Wi-Fi": (3, [("Ubiquiti", ["UniFi U6 Lite", "UniFi U6 Pro"], 100, 180),
                        ("HPE Aruba", ["Instant On AP22"], 150, 250)], False),
}
VERSIONS_OS = ["Windows 11 Pro 23H2", "Windows 11 Pro 24H2", "Windows 10 Pro 22H2"]
PREFIXES_NOM = {"PC fixe": "PC", "PC portable": "PCP", "Écran": "ECR",
                "Imprimante": "IMP", "Vidéoprojecteur": "VP", "Tablette": "TAB",
                "Switch": "SW", "Borne Wi-Fi": "WIFI"}
CONSOMMABLES_IMPRIMANTE = [("Toner noir", 4, 8), ("Toner cyan", 6, 12),
                           ("Toner magenta", 6, 12), ("Toner jaune", 6, 12),
                           ("Tambour", 12, 24), ("Kit de maintenance", 18, 36)]
COMMENTAIRES = [None, None, None, "Clavier remplacé", "Écran secondaire à prévoir",
                "Poste partagé", "Batterie fatiguée", "Ventilateur bruyant",
                "Prêté temporairement", "À renouveler l'an prochain"]

def date_aleatoire(debut: date, fin: date) -> date:
    return debut + timedelta(days=random.randint(0, (fin - debut).days))


def numero_serie_unique(deja: set) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    while True:
        ns = "DEMO" + "".join(random.choice(alphabet) for _ in range(8))
        if ns not in deja:
            deja.add(ns)
            return ns


def usager_aleatoire(categorie: str):
    if categorie in ("Switch", "Borne Wi-Fi", "Imprimante", "Vidéoprojecteur"):
        return None
    if random.random() < 0.4:
        return f"Poste {random.choice(SERVICES)}"
    return f"{random.choice(PRENOMS)} {random.choice(NOMS)}"


def creer_comptes(session: Session):
    for email, role in COMPTES_DEMO:
        session.add(User(
            email=email,
            mdp=hash_password(MDP_DEMO),
            role=role,
            doit_changer_mdp=False,
            totp_secret=TOTP_SECRET_DEMO,
            totp_active=True,
        ))
    for nom, label in PERMISSIONS_PAR_DEFAUT:
        session.add(Permission(nom=nom, label=label,
                               actif_pour_technicien=nom in PERMISSIONS_TECHNICIEN))


def creer_equipements(session: Session) -> list[Equipement]:
    aujourd_hui = date.today()
    categories = list(CATALOGUE)
    poids = [CATALOGUE[c][0] for c in categories]
    series, compteurs, equipements = set(), {}, []

    for _ in range(NB_EQUIPEMENTS):
        categorie = random.choices(categories, weights=poids)[0]
        _, marques, avec_os = CATALOGUE[categorie]
        marque, modeles, pmin, pmax = random.choice(marques)
        compteurs[categorie] = compteurs.get(categorie, 0) + 1

        # graphique du dashboard alimenté
        if random.random() < 0.2:
            installe = date_aleatoire(date(aujourd_hui.year, 1, 1), aujourd_hui)
        else:
            installe = date_aleatoire(aujourd_hui - relativedelta(years=6), aujourd_hui)

        eq = Equipement(
            nom=f"{PREFIXES_NOM[categorie]}-{compteurs[categorie]:03d}",
            lieu=random.choice(LIEUX),
            usager=usager_aleatoire(categorie),
            categorie=categorie,
            marque=marque,
            modele=random.choice(modeles),
            numero_serie=numero_serie_unique(series),
            date_installation=installe,
            etat=random.choices(["fonctionnel", "en réparation", "hors service"],
                                weights=[80, 10, 10])[0],
            salle=random.choice(SALLES),
            commentaire=random.choice(COMMENTAIRES),
            version_os=random.choice(VERSIONS_OS) if avec_os else None,
            cout=f"{random.randint(pmin, pmax)}.00",
            dans_corbeille=random.random() < 0.05,
        )
        session.add(eq)
        equipements.append(eq)
    session.flush()  # récupère les id
    return equipements


def creer_garanties(session: Session, equipements: list[Equipement]):
    for eq in equipements:
        if random.random() < 0.75:
            duree = random.choice([12, 24, 36, 36, 60])
            session.add(Garantie(
                equipement_id=eq.id,
                date_debut=eq.date_installation,
                duree_mois=duree,
                date_fin=eq.date_installation + relativedelta(months=duree),
            ))


def creer_consommables(session: Session, equipements: list[Equipement]) -> list[Consommable]:
    aujourd_hui = date.today()
    consommables = []
    for eq in equipements:
        if eq.categorie != "Imprimante" or eq.dans_corbeille:
            continue
        couleur = "MFC" in eq.modele or "ci" in eq.modele or "Cdw" in eq.modele or "C3326" in eq.modele
        for type_c, dmin, dmax in CONSOMMABLES_IMPRIMANTE:
            if not couleur and type_c in ("Toner cyan", "Toner magenta", "Toner jaune"):
                continue
            duree = random.randint(dmin, dmax)
            # Un ancien consommable déjà remplacé, puis le consommable en cours
            ancien_debut = aujourd_hui - relativedelta(months=duree * 2)
            ancien = Consommable(equipement_id=eq.id, type_consommable=type_c,
                                 lieu=eq.lieu, salle=eq.salle,
                                 date_installation=ancien_debut,
                                 duree_estimee_mois=duree, remplace=True)
            # Date d'installation répartie pour obtenir des statuts variés
            debut = aujourd_hui - timedelta(days=random.randint(0, int(duree * 30 * 1.1)))
            actuel = Consommable(equipement_id=eq.id, type_consommable=type_c,
                                 lieu=eq.lieu, salle=eq.salle,
                                 date_installation=max(debut, ancien_debut + timedelta(days=1)),
                                 duree_estimee_mois=duree, remplace=False)
            session.add_all([ancien, actuel])
            consommables.append((ancien, actuel))
    session.flush()
    return consommables


def creer_historique(session: Session, equipements, consommables):
    emails = [c[0] for c in COMPTES_DEMO[:2]]
    for eq in equipements:
        session.add(Historique(equipement_id=eq.id, date_action=eq.date_installation,
                               action="Ajout", utilisateur=random.choice(emails),
                               commentaire="Ajout au parc", nom_equipement=eq.nom))
        if eq.etat != "fonctionnel" or random.random() < 0.15:
            session.add(Historique(
                equipement_id=eq.id,
                date_action=date_aleatoire(eq.date_installation, date.today()),
                action="Changement", utilisateur=random.choice(emails),
                commentaire=f"État : {eq.etat}" if eq.etat != "fonctionnel" else "Changement de salle",
                nom_equipement=eq.nom))
        if eq.dans_corbeille:
            session.add(Historique(equipement_id=eq.id, date_action=date.today() - timedelta(days=random.randint(1, 60)),
                                   action="Suppression", utilisateur=emails[0],
                                   commentaire="Matériel obsolète", nom_equipement=eq.nom))
    for ancien, actuel in consommables:
        session.add(Historique(equipement_id=actuel.equipement_id, consommable_id=ancien.id,
                               date_action=actuel.date_installation, action="Remplacement",
                               utilisateur=random.choice(emails),
                               commentaire="Remplacement du consommable",
                               nom_equipement=actuel.type_consommable))


def creer_logs_connexion(session: Session):
    maintenant = datetime.now()
    for _ in range(60):
        email = random.choice([c[0] for c in COMPTES_DEMO] + ["inconnu@demo.local"])
        session.add(LogConnexion(
            email=email,
            date_action=maintenant - timedelta(minutes=random.randint(10, 60 * 24 * 30)),
            succes=email != "inconnu@demo.local" and random.random() < 0.9,
            ip=f"10.0.{random.randint(0, 5)}.{random.randint(2, 250)}",
        ))


def main():
    parser = argparse.ArgumentParser(description="Remplit la base avec des données de démo fictives.")
    parser.add_argument("--reset", action="store_true",
                        help="Supprime TOUTES les données existantes avant de générer la démo.")
    args = parser.parse_args()
    random.seed(GRAINE)

    if args.reset:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        if session.exec(select(Equipement)).first() or session.exec(select(User)).first():
            print("La base contient déjà des données. Relancez avec --reset pour la remplacer.")
            sys.exit(1)

        for nom in LIEUX:
            session.add(Lieu(nom=nom))
        creer_comptes(session)
        equipements = creer_equipements(session)
        creer_garanties(session, equipements)
        consommables = creer_consommables(session, equipements)
        creer_historique(session, equipements, consommables)
        creer_logs_connexion(session)
        session.commit()

    print(f"Base de démo créée : {len(equipements)} équipements, {len(LIEUX)} lieux, "
          f"{len(consommables) * 2} consommables.")
    print(f"Comptes (mot de passe : {MDP_DEMO}) : " + ", ".join(e for e, _ in COMPTES_DEMO))
    print(f"Clé 2FA à ajouter dans Google Authenticator : {TOTP_SECRET_DEMO}")


if __name__ == "__main__":
    main()