import os
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.models import Equipement, Historique
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
from app.dependencies import templates, get_session, logger
from dotenv import load_dotenv
from datetime import date

router = APIRouter()
load_dotenv()


class Poste(BaseModel):
    numero_serie: str
    nom: str
    marque: str
    modele: str
    version_os: Optional[str] = None
    usager: Optional[str] = None
    lieu: Optional[str] = None
    salle: Optional[str] = None
    categorie: Optional[str] = None
    date_installation: Optional[date] = None

@router.post('/script')
def script( poste: Poste, request: Request, session: Session = Depends(get_session), x_api_key: str = Header(...)):
    if x_api_key != os.getenv("AGENT_API_KEY"):
        raise HTTPException(status_code=403, detail="pas la bonne clée")
    existing = session.exec(select(Equipement).where(Equipement.numero_serie == poste.numero_serie)).first()
    if not existing:
        nouvel_equipement = Equipement(
            numero_serie = poste.numero_serie,
            nom = poste.nom,
            marque = poste.marque,
            modele = poste.modele,
            version_os = poste.version_os,
            usager = poste.usager,
            lieu = poste.lieu,
            salle = poste.salle,
            categorie = poste.categorie,
            date_installation = poste.date_installation,
            etat = "à vérifier"
        )
        session.add(nouvel_equipement)
        session.commit()
        session.refresh(nouvel_equipement)
        historique = Historique(
            equipement_id = nouvel_equipement.id,
            date_action = date.today(),
            action = "Ajout automatique",
            utilisateur = "Agent réseau",
            commentaire = "Créé via script d'inventaire automatique",
            nom_equipement = nouvel_equipement.nom
        )
        session.add(historique)
        session.commit()
    else:
        existing.marque = poste.marque
        existing.modele = poste.modele
        existing.version_os = poste.version_os
        existing.usager = poste.usager  
        existing.lieu = poste.lieu
        existing.salle = poste.salle
        session.add(existing)
        session.commit()
        historique = Historique(
            equipement_id = existing.id,
            date_action = date.today(),
            action = "Mise à jour automatique",
            utilisateur = "Agent réseau",
            commentaire = "Créé via script d'inventaire automatique",
            nom_equipement = existing.nom,
        )
        session.add(historique)
        session.commit()
    return JSONResponse(content={"statut": "ok"})
    



