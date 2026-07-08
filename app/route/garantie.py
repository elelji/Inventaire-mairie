from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from app.models import Equipement, Garantie, User, Lieu
from datetime import date
from sqlmodel import Session, select, func
from dateutil.relativedelta import relativedelta
from app.dependencies import templates, get_session, engine, logger
from app.auth import require_permission, require_login

router = APIRouter()

#GET - Garanties
@router.get("/garanties")
async def garanties(request: Request, current_user: User = Depends(require_login),session: Session = Depends(get_session)):
    garanties = session.exec(select(Garantie)).all()
    garanties_avec_statut = []
    print(f"Nombre de garanties : {len(garanties)}")
    for g in garanties:
        print(g.date_fin, type(g.date_fin))
        if g.date_fin < date.today():
            statut = "expiré"
        elif g.date_fin < date.today() + relativedelta(months=3):
            statut = "bientôt"
        else:
            statut = "ok"
        garanties_avec_statut.append({"garantie": g, "statut": statut})
    count_ok = sum(1 for item in garanties_avec_statut if item["statut"] == "ok")
    count_warn = sum(1 for item in garanties_avec_statut if item["statut"] == "bientôt")
    count_danger = sum(1 for item in garanties_avec_statut if item["statut"] == "expiré")
    return templates.TemplateResponse(
        request=request,
        name="garanties.html",
        context={
    "garanties_avec_statut": garanties_avec_statut,
    "count_ok": count_ok,
    "count_warn": count_warn,
    "count_danger": count_danger,
    "total_items": len(garanties_avec_statut)
        }
    )

#GET - statistiques
@router.get("/statistiques")
async def statistiques(request: Request, current_user: User = Depends(require_login), session: Session = Depends(get_session)):
    try:
        # 1. Tes requêtes globales optimisées
        equipement_lieu = session.exec(
            select(Equipement.lieu, func.count(Equipement.id)).group_by(Equipement.lieu)
        ).all()
        
        equipement_etat = session.exec(
            select(Equipement.etat, func.count(Equipement.id)).group_by(Equipement.etat)
        ).all()
        
        equipement_categorie = session.exec(
            select(Equipement.categorie, func.count(Equipement.id)).group_by(Equipement.categorie)
        ).all()
        
        installations_annee = session.exec(
            select(func.strftime('%Y', Equipement.date_installation), func.count(Equipement.id))
            .where(Equipement.date_installation != None)
            .group_by(func.strftime('%Y', Equipement.date_installation))
        ).all()
        
        # 2. Récupération des garanties VPI
        garanties_vpi = session.exec(
            select(Garantie).join(Equipement).where(Equipement.categorie == "VPI")
        ).all()
        
        # 3. Calcul dynamique des statuts de garanties (Correction indentation ici)
        garanties_avec_statut = []
        today = date.today()
        dans_3_mois = today + relativedelta(months=3)
        
        for g in garanties_vpi:
            if g.date_fin < today:
                statut = "expiré"
            elif g.date_fin < dans_3_mois:
                statut = "bientôt"
            else:
                statut = "ok"
            garanties_avec_statut.append({"garantie": g, "statut": statut})
        
        # 4. Tes compteurs
        count_ok = sum(1 for item in garanties_avec_statut if item["statut"] == "ok")
        count_warn = sum(1 for item in garanties_avec_statut if item["statut"] == "bientôt")
        count_danger = sum(1 for item in garanties_avec_statut if item["statut"] == "expiré")

        # 5. Envoi au template Jinja
        return templates.TemplateResponse(
            request=request,
            name="statistiques.html",
            context={
                "equipement_lieu": equipement_lieu,
                "equipement_etat": equipement_etat,
                "equipement_categorie": equipement_categorie,
                "installations_annee": installations_annee,
                "count_ok": count_ok,
                "count_warn": count_warn,
                "count_danger": count_danger,
                "total_items": len(garanties_avec_statut)
            }
        )
    except Exception as e:
        print(f"ERREUR STATISTIQUES : {e}")
        raise
        