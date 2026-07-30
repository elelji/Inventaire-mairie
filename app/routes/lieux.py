from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import Equipement, User, Lieu
from sqlmodel import Session, select
from app.dependencies import templates, get_session, engine, logger
from app.auth import require_permission, require_login
from sqlalchemy import func

router = APIRouter()

#GET LIEUX - LISTER LES LIEUX
@router.get("/admin/lieux")
def voir_lieux(request: Request,current_user: User = Depends(require_login),session: Session = Depends(get_session)):
    query = (
        select(Lieu, func.count(Equipement.id).label("total_equipements"))
        .outerjoin(Equipement, Equipement.lieu == Lieu.nom)
        .group_by(Lieu.id)
    )
    results = session.exec(query).all()
    lieux_list = []
    for lieu, count in results:
        lieux_list.append({"lieu": lieu, "total": count})
    erreur = request.query_params.get("erreur")
    return templates.TemplateResponse(
        request=request,
        name="admin_lieux.html",
        context={"lieux": lieux_list, "erreur": erreur}
    )

#POST - AJT LIEUX
@router.post("/admin/lieux/ajouter")
def ajouter_lieu(
    nom: str = Form(), 
    current_user: User = Depends(require_permission("ajouter_ecole")), 
    session: Session = Depends(get_session)
):
    existing = session.exec(select(Lieu).where(Lieu.nom == nom)).first()
    lieu = Lieu(nom=nom)
    if not existing:
        session.add(lieu)
        session.commit()
    return RedirectResponse(
        url="/admin/lieux", 
        status_code=303
        )

#POST - RENOMMER UNE ÉCOLE
@router.post("/admin/lieux/renommer/{lieu_id}")
def renommer_lieu(
    lieu_id: int, 
    nouveau_nom: str = Form(), 
    current_user: User = Depends(require_permission("modifier_lieu")), 
    session: Session = Depends(get_session)
):
    lieu = session.get(Lieu, lieu_id)
    if not lieu:
        raise HTTPException(status_code=404)

    ancien_nom = lieu.nom
    lieu.nom = nouveau_nom
    session.add(lieu)
    # Met à jour tous les équipements qui pointaient sur l'ancien nom
    equipements = session.exec(select(Equipement).where(Equipement.lieu == ancien_nom)).all()
    for e in equipements:
        e.lieu = lieu.nom
        session.add(e)

    session.commit()
    return RedirectResponse(url="/admin/lieux", status_code=303)

#POST - SUPPRESSION D'UN LIEU
@router.post("/admin/lieux/supprimer/{lieu_id}")
def supprimer_lieu(
    lieu_id: int,
    current_user: User = Depends(require_permission("modifier_lieu")),
    session: Session = Depends(get_session)
):
    lieu = session.get(Lieu, lieu_id)
    if not lieu:
        raise HTTPException(status_code=404, detail="Lieu introuvable")

    # Sécurité : on bloque si des équipements sont encore rattachés à ce lieu
    equipements_lies = session.exec(select(Equipement).where(Equipement.lieu == lieu.nom)).all()
    if equipements_lies:
        return RedirectResponse(
            url=f"/admin/lieux?erreur=Impossible de supprimer {lieu.nom} : {len(equipements_lies)} équipement(s) y sont encore rattachés",
            status_code=303
        )

    session.delete(lieu)
    session.commit()
    return RedirectResponse(url="/admin/lieux", status_code=303)