from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query 
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models import Equipement, User, Historique, Lieu, Garantie, Consommable
from datetime import date
from sqlmodel import Session, select, or_
from typing import Optional
from app.dependencies import templates, get_session, engine, logger
from app.auth import require_permission,require_login

router = APIRouter()

@router.get('/consommables', response_class=HTMLResponse)
def liste_consommables(
    request: Request, 
    current_user: User = Depends(require_login),
    session: Session = Depends(get_session),
):
    statement = select(Consommable)
    consommable = session.exec(statement).all()
    return templates.TemplateResponse(
        request=request,
        name="consommables.html",
        context={"consommables":consommable}
    )

@router.post('/consommables')
def liste_consommables_form(
    request: Request,
    current_user: User = Depends(require_permission("creer_consommable")),
    session: Session = Depends(get_session),
    equipement_id: Optional[int] = Form(default=None),
    type_consommable: str = Form(),
    lieu: Optional[str] = Form(default=None),
    salle: Optional[str] = Form(default=None), 
    date_installation: date = Form(),
    duree_estimee_mois: int = Form(),
):
    consommable = Consommable(
        equipement_id=equipement_id,
        type_consommable=type_consommable,
        lieu=lieu,
        salle=salle,
        date_installation=date_installation,
        duree_estimee_mois=duree_estimee_mois
    )
    try:
        session.add(consommable)
        session.commit()
        logger.info('Un nouvel consommable est enregistré')
        return RedirectResponse(url="/", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur d'enregistrement: {exc}")
        return templates.TemplateResponse(
            request=request,
            name="consommables.html",
            context={"erreur": "Erreur lors de l'enregistrement du consommable"}
            )

@router.get('/api/equipement')
def get_equipement(numero_serie: str = Query(default=""), session: Session = Depends(get_session)):
    query = select(Equipement.id, Equipement.lieu, Equipement.salle)
    query = query.where(Equipement.numero_serie == numero_serie)
    result = session.exec(query).all()
    return JSONResponse([{"id": i, "lieu": l, "salle": s} for i, l, s in result])

@router.post('/consommables/{consommable_id}/remplacer')
def consommable_remplacer(
    consommable_id: int, 
    request: Request, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(require_permission("remplacer_consommable"))
):
    consommable = session.exec(select(Consommable).where(Consommable.id == consommable_id)).first()
    try:
        consommable.remplace = True
        session.add(consommable)
        historique = Historique(
            consommable_id=consommable_id,
            date_action=date.today(),
            action="Remplacement",
            utilisateur=current_user.email,
            nom_equipement=consommable.type_consommable,
            commentaire="Remplacement du consommable",
        )
        session.add(historique)
        nouveau_consommable = Consommable(
            type_consommable=consommable.type_consommable,
            equipement_id=consommable.equipement_id,
            lieu=consommable.lieu,
            salle=consommable.salle,
            duree_estimee_mois=consommable.duree_estimee_mois,
            date_installation=date.today(),
        )
        session.add(nouveau_consommable)
        session.commit()
        logger.info('Consommable remplacé')
        return RedirectResponse(url="/", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur de remplacement {exc}")
        return HTMLResponse(content="Le consommable ne peut pas être remplacé", status_code=500)

