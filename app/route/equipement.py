from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models import Equipement, User, Historique, Lieu, Garantie
from datetime import date
from sqlmodel import Session, select, or_
from typing import Optional
from app.dependencies import templates, get_session, engine, logger
from app.auth import require_permission,require_login


router = APIRouter()

#GET /equipements — lister tous les équipements
@router.get('/equipement', response_class=HTMLResponse)
async def equipement(request:Request, current_user: User = Depends(require_login),session: Session = Depends(get_session),
    search : str = "",
    etat : str = "",
    lieu : str = "",
    categorie : str = "",
):
    statement=select(Equipement)
    statement = statement.where(Equipement.dans_corbeille == False)
    if search:
        statement = statement.where(Equipement.nom.contains(search))
    if etat:
        statement = statement.where(Equipement.etat == etat)
    if lieu:
        statement = statement.where(Equipement.lieu == lieu)
    if categorie:
        statement = statement.where(Equipement.categorie == categorie)
    equipement = session.exec(statement).all()
    categories = session.exec(select(Equipement.categorie).distinct()).all()
    lieux = session.exec(select(Equipement.lieu).distinct()).all()
    return templates.TemplateResponse(
        request=request,
        name="equipements.html",
        context={
            "equipements": equipement,
            "search": search,
            "etat": etat,
            "lieu": lieu,
            "categorie": categorie,
            "categories": categories,
            "lieux": lieux,
        }
    )

#GET /equipements/{id} — voir un équipement
@router.get("/equipement/{equipement_numero_serie}")
async def read_equipement(equipement_numero_serie: str, request: Request, session: Session = Depends(get_session)):
    equipement = session.exec(select(Equipement).where(Equipement.numero_serie == equipement_numero_serie)).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Ce numéro série n'existe pas")

    historique = session.exec(
        select(Historique)
        .where(Historique.equipement_id == equipement.id)
        .order_by(Historique.id.desc())
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="detail_equipement.html",
        context={"equipement": equipement, "historique": historique}
    )

#GET /formulaire equipements - afficher le formulaire d'ajt équipement
@router.get("/create_equipement")
async def create_equipement(request:Request, current_user: User = Depends(require_login), session: Session = Depends(get_session)):
    categories = session.exec(select(Equipement.categorie).distinct()).all()
    lieux = session.exec(select(Lieu.nom).distinct()).all()
    return templates.TemplateResponse(            
        request=request,
        name="form_equipement.html",                         
        context={
            "categories": categories,
            "lieux": lieux,
        }
    )

#GET /formulaire equipements - afficher le formulaire de modification
@router.get("/edit_equipement/{equipement_numero_serie}")
async def edit_equipement_form(equipement_numero_serie: str, request:Request, session: Session = Depends(get_session)):
    equipement = session.exec(select(Equipement).where(Equipement.numero_serie == equipement_numero_serie)).first()
    categories = session.exec(select(Equipement.categorie).distinct()).all()
    lieux = session.exec(select(Lieu.nom).distinct()).all()
    return templates.TemplateResponse(            
        request=request,
        name="form_equipement.html",                         
        context={
            "equipement":equipement,
            "categories": categories,
            "lieux": lieux,
        }
    )

#POST /equipements — ajouter un équipement
@router.post("/create_equipement")
async def create_equipement(
    request:Request, 
    current_user: User = Depends(require_permission("ajouter_equipement")), 
    session: Session = Depends(get_session),
    nom: str = Form(),
    lieu: str = Form(),
    usager: str = Form(),
    categorie: str = Form(default=""),
    marque: str = Form(),
    modele: str = Form(),
    numero_serie: str = Form(),
    date_installation: Optional[date] = Form(default=None),
    etat: str = Form(),
    salle: str = Form(),
    commentaire: str = Form(default=""),
    nouvelle_categorie: str = Form(default=""),
    nouvelle_salle: str = Form(default=""),
    ):
    existing = session.exec(select(Equipement).where(Equipement.numero_serie == numero_serie)).first()
    if existing:
        raise HTTPException(status_code=404, detail="Ce numéro série est déjà enregistré")
    if nouvelle_categorie:
        categorie = nouvelle_categorie
    if salle == "__nouvelle__" and nouvelle_salle:
        salle = nouvelle_salle

    #recréer l'objet
    equipement = Equipement(
        nom=nom,
        lieu=lieu,
        usager=usager,
        categorie=categorie,
        marque=marque,
        modele=modele,
        numero_serie=numero_serie,
        date_installation=date_installation,
        etat=etat,
        salle=salle,
        commentaire=commentaire,
    )
    try:
        session.add(equipement)
        session.commit()  # ← commit d'abord
        session.refresh(equipement)  # ← pour récupérer l'id généré
        historique = Historique(
                equipement_id=equipement.id,
                date_action=date.today(),
                action="Ajout",
                utilisateur=current_user.email,
                commentaire="",
                nom_equipement=equipement.nom
            )
        session.add(historique)
        session.commit()
        logger.info('Un nouvel equipement est enregistré')
        return RedirectResponse(url="/equipement", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur d'enregistrement: {exc}")
        return templates.TemplateResponse(
            request=request,
            name="form_equipement",
            context={}
            )
    
#PUT /equipements/{id} — modifier
@router.post("/change_equipement/{equipement_numero_serie}")
async def change_equipement(
    equipement_numero_serie: str, 
    request:Request, current_user: User = Depends(require_permission("modifier_equipement")), 
    session: Session = Depends(get_session),
    nom: str = Form(),
    lieu: str = Form(),
    usager: str = Form(),
    categorie: str = Form(),
    marque: str = Form(),
    modele: str = Form(),
    numero_serie: str = Form(),
    date_installation: date = Form(),
    etat: str = Form(),
    salle: str = Form(),
    commentaire: str = Form(),
    nouvelle_categorie: str = Form(default=""),
    nouvelle_salle: str = Form(default=""),
):
        equipement = session.exec(select(Equipement).where(Equipement.numero_serie == equipement_numero_serie)).first()
        if not equipement:
            raise HTTPException(status_code=404, detail="Ce numéro série n'existe pas")
        if nouvelle_categorie:
            categorie = nouvelle_categorie
        if salle == "__nouvelle__" and nouvelle_salle:
            salle = nouvelle_salle
        try:
            equipement.nom=nom
            equipement.lieu=lieu
            equipement.usager=usager
            equipement.categorie=categorie
            equipement.marque=marque
            equipement.modele=modele
            equipement.numero_serie=numero_serie
            equipement.date_installation=date_installation
            equipement.etat=etat
            equipement.salle=salle
            equipement.commentaire=commentaire
            session.add(equipement)
            session.commit()  # ← commit d'abord
            session.refresh(equipement)  # ← pour récupérer l'id généré
            historique = Historique(
                    equipement_id=equipement.id,
                    date_action=date.today(),
                    action="Changement",
                    utilisateur=current_user.email,
                    commentaire="",
                    nom_equipement=equipement.nom
                )
            session.add(historique)
            session.commit()
            logger.info('Equipement modifié')
            return RedirectResponse(url="/equipement", status_code=303)
        except Exception as exc:
            logger.error(f"Erreur de modification {exc}")

        return templates.TemplateResponse(
            request=request,
            name="form_equipement.html",
            context={"equipement": equipement}
            )

#DELETE /equipements/{id} — supprimer
@router.post("/delete_equipement/{equipement_numero_serie}")
async def delete_equipement(
    equipement_numero_serie: str,
    request:Request, 
    commentaire_suppression: str = Form(default=""), 
    current_user: User = Depends(require_permission("supprimer_equipement")), 
    session: Session = Depends(get_session)
    ):
        equipement = session.exec(select(Equipement).where(Equipement.numero_serie == equipement_numero_serie)).first()
        if not equipement:
            raise HTTPException(status_code=404, detail="Ce numéro série n'existe pas")
        try:
            equipement.dans_corbeille = True
            session.add(equipement)
            historique = Historique(
                equipement_id=equipement.id,
                date_action=date.today(),
                action="Suppression",
                utilisateur=current_user.email,
                commentaire=commentaire_suppression,
                nom_equipement=equipement.nom
            )
            session.add(historique)
            session.commit()
            logger.info('Equipement supprimés')
            return RedirectResponse(url="/equipement", status_code=303)
        except Exception as exc:
            logger.error(f"Erreur de suppression {exc}")
            return HTMLResponse(content="L'equipement ne peut pas être supprimé", status_code=500)


# GET /HISTORIQUE
@router.get("/history",response_class=HTMLResponse)
async def history(request: Request, current_user: User = Depends(require_login),session: Session = Depends(get_session)):
    statement = (
        select(Historique, Equipement)
        .join(Equipement, Historique.equipement_id == Equipement.id, isouter=True)
        .order_by(Historique.id.desc())
    )
    equipement_histo = session.exec(statement).all()

    return templates.TemplateResponse(
        request=request,
        name="historique.html",
        context={"equipement_histo": equipement_histo}
    )

@router.get("/api/search")
def search_bar(request: Request, session: Session = Depends(get_session), q: str = ""):
    mots = q.split()
    statement = select(Equipement).where(Equipement.dans_corbeille == False)
    for mot in mots:
        statement = statement.where(
            or_(
                Equipement.nom.contains(mot),
                Equipement.lieu.contains(mot),
                Equipement.categorie.contains(mot),
                Equipement.salle.contains(mot),
            )
        )
    equipements = session.exec(statement.limit(8)).all()
    lieux = session.exec(select(Lieu).where(Lieu.nom.contains(q)).limit(5)).all()
    garanties = session.exec(select(Garantie, Equipement).where(Garantie.equipement_id == Equipement.id).where(Equipement.nom.contains(q)).limit(5)).all()
    return JSONResponse(content={
        "equipements": [{"nom": e.nom, "numero_serie": e.numero_serie, "lieu": e.lieu, "categorie": e.categorie, "etat": e.etat,}for e in equipements],
        "lieux": [{"nom": l.nom,}for l in lieux],
        "garanties": [{"nom": e.nom,"date_fin": str(g.date_fin),"lieu": e.lieu,}for g, e in garanties],
    })

