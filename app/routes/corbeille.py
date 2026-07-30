from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import Equipement, Historique, User
from sqlmodel import Session, select
from app.dependencies import templates, get_session, engine, logger
from app.auth import require_permission, require_login
from datetime import date

router = APIRouter()

#GET /corbeilles - corbeille:suppression
@router.get('/corbeille', response_class=HTMLResponse)
async def corbeille(request:Request, current_user: User = Depends(require_permission("acces_corbeille")),session: Session = Depends(get_session),):
    statement=select(Equipement)
    statement = statement.where(Equipement.dans_corbeille == True)
    equipement = session.exec(statement).all()
    return templates.TemplateResponse(
        request=request,
        name="corbeille.html",
        context={"equipements": equipement,}
    )


#POST /restaurer-equipements : restauration
@router.post('/restaurer-equipements/{equipement_numero_serie}')
async def restaurer_equipements(equipement_numero_serie: str, request:Request, current_user: User = Depends(require_permission("acces_corbeille")), session: Session = Depends(get_session),):
    equipement = session.exec(select(Equipement).where(Equipement.numero_serie == equipement_numero_serie)).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    equipement.dans_corbeille = False
    session.add(equipement)
    historique = Historique(
        equipement_id=equipement.id,
        date_action=date.today(),
        action="Restauration",
        utilisateur=current_user.email,
        commentaire="",
        nom_equipement=equipement.nom
    )
    session.add(historique)
    session.commit()
    return RedirectResponse(url="/corbeille", status_code=303)



#POST /supprimer définitivement
@router.post("/supprimer_definitif/{equipement_numero_serie}")
async def supprimer_definitif(equipement_numero_serie: str, request: Request, current_user: User = Depends(require_permission("supprimer_equipement")), session: Session = Depends(get_session)):
    equipement = session.exec(select(Equipement).where(Equipement.numero_serie == equipement_numero_serie)).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    # On détache les entrées d'historique de l'équipement (sécurité, même si pas de cascade active)
    historiques = session.exec(select(Historique).where(Historique.equipement_id == equipement.id)).all()
    for h in historiques:
        h.equipement_id = None
        session.add(h)

    session.delete(equipement)
    session.commit()

    return RedirectResponse(url="/corbeille", status_code=303)
