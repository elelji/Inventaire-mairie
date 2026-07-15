import os
from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel
from sqlmodel import Session, select
from app.models import Equipement
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
from app.dependencies import templates, get_session, logger
from dotenv import load_dotenv

router = APIRouter()

class Poste(BaseModel):
    numero_serie: str
    marque: str
    modele: str
    version_os: Optional[str] = None
    usager: Optional[str] = None

@router.post('/script')
def script( poste: Poste, request: Request, session: Session = Depends(get_session), x_api_key: str = Header(...)):
    if x_api_key != os.getenv("AGENT_API_KEY"):
        raise HTTPException(status_code=403, detail="pas la bonne clée")
    existing = session.exec(select(Equipement).where(Equipement.numero_serie == poste.numero_serie)).first()
    if not existing:
        return HTMLResponse(content="L'equipement n'existe pas", status_code=404)
    existing.marque = poste.marque
    existing.modele = poste.modele
    existing.version_os = poste.version_os
    existing.usager = poste.usager  
    session.add(existing)
    session.commit() 
    return JSONResponse(content={"statut": "ok"})