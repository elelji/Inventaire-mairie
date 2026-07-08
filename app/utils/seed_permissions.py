from sqlmodel import Session, select
from app.dependencies import engine
from app.models import Permission

PERMISSIONS_PAR_DEFAUT = [
    ("ajouter_ecole", "Ajouter une nouvelle école"),
    ("creer_nouvel_utilisateur", "Créer un nouvel utilisateur ")
    ("modifier_nom_ecole", "Modifier le nom d'une école"),
    ("generer_pdf", "Générer un PDF"),
    ("ajouter_equipement", "Ajouter un équipement"),
    ("modifier_equipement", "Modifier un équipement"),
    ("ajouter_categorie", "Ajouter une catégorie"),
    ("supprimer_equipement", "Supprimer un équipement"),
    ("modifier_utilisateur", "Modifier un utilisateur et ses rôles"),
    ("acces_corbeille", "Accès à la corbeille"),
    ("consultation_sortie_inventaire", "Consulter sortie d'inventaire"),
    ("generer_sortie_inventaire", "Générer un PDF de sortie d'inventaire"),
    ("voir_utilisateur", "Voir les utilisateurs"),
    ("supprimer_utilisateur", "Supprimer un utilisateur"),
    ("consulter_logs_co", "Consulter les logs de connexion"),
    ("remplacer_consommable", "Remplacer un consommable"),
    ("creer_consommable", "Créer un consommable"),
]

if __name__ == "__main__":
    with Session(engine) as session:
        for nom, label in PERMISSIONS_PAR_DEFAUT:
            existing = session.exec(select(Permission).where(Permission.nom == nom)).first()
            if not existing:
                session.add(Permission(nom=nom, label=label, actif_pour_technicien=False))
        session.commit()
        print("Permissions créées.")