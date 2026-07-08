import asyncio
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select
from app.models import Garantie, Equipement
from app.dependencies import engine


def verifier_garantie_lenovo(serial_number):
    """
    Interroge l'API Lenovo (non officielle mais largement utilisée par la
    communauté IT) pour récupérer les infos de garantie d'un numéro de série.
    """
    url = "http://supportapi.lenovo.com/v2.5/warranty"
    params = {"Serial": serial_number}

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        return {"Statut": "Erreur", "Message": f"Erreur réseau : {e}"}

    if response.status_code != 200:
        return {"Statut": "Erreur", "Message": f"Code HTTP {response.status_code}"}

    try:
        data = response.json()
    except ValueError:
        return {"Statut": "Erreur", "Message": "Réponse non-JSON reçue"}

    garanties = data.get("Warranty", [])
    if not garanties:
        return {"Statut": "Erreur", "Message": "Aucune garantie trouvée pour ce numéro de série"}

    dates_debut = [g["Start"] for g in garanties if g.get("Start")]
    dates_fin = [g["End"] for g in garanties if g.get("End")]

    if not dates_debut or not dates_fin:
        return {"Statut": "Erreur", "Message": "Dates de garantie manquantes dans la réponse"}

    return {
        "Statut": "Succès",
        # On garde la garantie la plus large : début le plus ancien, fin la plus tardive
        "Début de Garantie": min(dates_debut),
        "Fin de Garantie": max(dates_fin),
    }


async def scraper_garanties_lenovo_background():
    await asyncio.sleep(2)  # laisse le serveur démarrer

    with Session(engine) as session:
        equipements = session.exec(
            select(Equipement).where(Equipement.marque.ilike("%lenovo%"))
        ).all()

        for eq in equipements:
            if not eq.numero_serie:
                continue

            result = verifier_garantie_lenovo(eq.numero_serie)

            if result["Statut"] == "Succès":
                try:
                    date_debut = datetime.strptime(result["Début de Garantie"][:10], "%Y-%m-%d").date()
                    date_fin = datetime.strptime(result["Fin de Garantie"][:10], "%Y-%m-%d").date()

                    delta = relativedelta(date_fin, date_debut)
                    duree_mois = delta.years * 12 + delta.months

                    garantie = session.exec(
                        select(Garantie).where(Garantie.equipement_id == eq.id)
                    ).first()

                    if not garantie:
                        garantie = Garantie(
                            equipement_id=eq.id,
                            date_debut=date_debut,
                            date_fin=date_fin,
                            duree_mois=duree_mois,
                        )
                        session.add(garantie)
                    else:
                        garantie.date_debut = date_debut
                        garantie.date_fin = date_fin
                        garantie.duree_mois = duree_mois

                    session.commit()
                    print(f"Garantie Lenovo enregistrée : {eq.numero_serie}")
                except Exception as e:
                    print(f"Erreur parsing garantie Lenovo {eq.numero_serie} : {e}")
            else:
                print(f"Échec garantie Lenovo {eq.numero_serie} : {result.get('Message')}")

            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(scraper_garanties_lenovo_background())