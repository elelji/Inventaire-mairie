import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select
from app.models import Garantie, Equipement
from app.dependencies import engine

def verifier_garantie_epson(serial_number):
    session = requests.Session()

    response = session.get(
        'https://warrantycheck.epson.eu/',
        headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
        verify=False
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    token = soup.find("input", attrs={"name": "__RequestVerificationToken"}).get("value")

    payload = {
        "SerialNumber": serial_number,
        "Country2Code": "FR",
        "__RequestVerificationToken": token
    }
    response_post = session.post(
        'https://warrantycheck.epson.eu/',
        data=payload,
        headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'referer': 'https://warrantycheck.epson.eu/'
        },
        verify=False
    )

    soup_post = BeautifulSoup(response_post.text, 'html.parser')

    def extraire(label):
        tag = soup_post.find(string=label)
        if tag:
            div_valeur = tag.parent.parent.find_next_sibling("div")
            if div_valeur:
                return div_valeur.find("p").text.strip()
        return "Inconnu"

    if "Model:" in response_post.text:
        return {
            "Statut": "Succès",
            "Modèle": extraire("Model:"),
            "Début de Garantie": extraire("Warranty Start:"),
            "Fin de Garantie": extraire("Warranty End:")
        }
    else:
        return {
            "Statut": "Erreur",
            "Message": "Mauvais numéro de série"
        }

async def scraper_garanties_background():
    await asyncio.sleep(2)  # laisse le serveur démarrer
    with Session(engine) as session:
        equipements = session.exec(
            select(Equipement).where(Equipement.marque.ilike("%epson%"))
        ).all()
        for eq in equipements:
            if not eq.numero_serie:
                continue
            result = verifier_garantie_epson(eq.numero_serie)
            if result["Statut"] == "Succès":
                try:
                    date_debut = datetime.strptime(result["Début de Garantie"], "%d.%m.%Y").date()
                    date_fin = datetime.strptime(result["Fin de Garantie"], "%d.%m.%Y").date()
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
                            duree_mois=duree_mois
                        )
                        session.add(garantie)
                    else:
                        garantie.date_debut = date_debut
                        garantie.date_fin = date_fin
                        garantie.duree_mois = duree_mois
                    session.commit()
                    print(f"Garantie enregistrée : {eq.numero_serie}")
                except Exception as e:
                    print(f"Erreur parsing garantie {eq.numero_serie} : {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(scraper_garanties_background())