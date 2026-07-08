from datetime import date, timedelta
from app.models import Consommable

def jours_ecouler_consommables(consommable: Consommable):
   difference = date.today()- consommable.date_installation
   return difference.days

def jours_restants_consommable(consommable: Consommable):  
    duree_totale_jours = consommable.duree_estimee_mois * 30
    reste = duree_totale_jours - jours_ecouler_consommables(consommable)
    return reste

def pourcentage_restant_consommable(consommable: Consommable):
    duree_totale_jours = consommable.duree_estimee_mois * 30
    pourcent_restant = (jours_restants_consommable(consommable) / duree_totale_jours) * 100
    return pourcent_restant

def statut_consommable(consommable: Consommable):
    pourcentage = pourcentage_restant_consommable(consommable)
    if pourcentage > 50:
        return "OK"
    elif pourcentage > 20 and pourcentage < 50:
        return "Bientôt épuisé"
    else :
        return "A remplacer"

def date_fin_estimee_consommable(consommable: Consommable):
    duree_totale_jours = consommable.duree_estimee_mois * 30
    return consommable.date_installation + timedelta(days=duree_totale_jours)

