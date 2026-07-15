#Tous mes imports
import os
import asyncio
from contextlib import asynccontextmanager
from app.utils.epson_scraper import scraper_garanties_background
from datetime import date
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .route import equipement, auth, admin, corbeille, lieux, export, manageengine, garantie, user, consommable, script
from app.models import Equipement, Garantie, Consommable, Historique, User, Lieu
from sqlmodel import Field, SQLModel, create_engine, Session, select, func
from app.dependencies import templates, get_session, engine, logger
from dateutil.relativedelta import relativedelta
from starlette.middleware.sessions import SessionMiddleware
from app.auth import require_login, get_current_user
import logging
from dotenv import load_dotenv

load_dotenv()
#fonction lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    asyncio.create_task(scraper_garanties_background())
    yield

#déclaration app => fastapi
app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"), max_age=28800)

#ajout de mes routes dans l'app
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(equipement.router)
app.include_router(admin.router)
app.include_router(lieux.router)
app.include_router(export.router)
app.include_router(garantie.router)
app.include_router(manageengine.router)
app.include_router(corbeille.router)
app.include_router(consommable.router)
app.include_router(script.router)


#FONCTION UTILITAIRE POUR METTRE LES CADENAS ET FLOUTTE SI PAS LES PERM
def get_template_context(request: Request, session: Session, user: User = None):
    return {
        "current_user": user,
        "can": lambda nom: user.has_perm(nom, session) if user else False
    }

@app.get("/")
def read_root(request: Request, current_user: User = Depends(require_login), session: Session = Depends(get_session), user: User | None = Depends(get_current_user)):
    equipements = session.exec(select(Equipement)).all()
    consommables = session.exec(select(Consommable).where(Consommable.remplace == False)).all()
    lieux = session.exec(select(Lieu)).all()
    total = len(session.exec(select(Equipement)).all())
    derniers = session.exec(select(Equipement).order_by(Equipement.id.desc()).limit(5)).all()
    fonctionnels = len(session.exec(select(Equipement).where(Equipement.etat == "fonctionnel")).all())
    hors_service = len(session.exec(select(Equipement).where(Equipement.etat == "hors service")).all())
    en_reparation = len(session.exec(select(Equipement).where(Equipement.etat == "en réparation")).all())
    categories_raw = session.exec(
        select(Equipement.categorie, func.count(Equipement.id)).group_by(Equipement.categorie)
    ).all()
    installations_annee = session.exec(
        select(Equipement.categorie, func.count(Equipement.id))
        .where(func.strftime('%Y', Equipement.date_installation) == str(date.today().year))
        .group_by(Equipement.categorie)
    ).all()
    aujourd_hui = date.today()
    debut_annee = date(aujourd_hui.year, 1, 1)
    fin_annee = date(aujourd_hui.year, 12, 31)
    pct_annee_ecoule = (aujourd_hui - debut_annee).days / (fin_annee - debut_annee).days
    garanties_raw = session.exec(select(Garantie)).all()
    garanties_dashboard = []
    for g in garanties_raw:
        if g.date_fin < date.today():
            statut = "expiré"
        elif g.date_fin < date.today() + relativedelta(months=3):
            statut = "bientôt"
        else:
            statut = "ok"
        garanties_dashboard.append({"garantie": g, "statut": statut})
    
    # Trier : expirés en premier, puis bientôt, puis ok
    ordre = {"expiré": 0, "bientôt": 1, "ok": 2}
    garanties_dashboard.sort(key=lambda x: (ordre[x["statut"]], x["garantie"].date_fin))
    garanties_dashboard = garanties_dashboard[:5]  # top 5
    contexte_securite = get_template_context(request, session, user)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "total": total,
            "fonctionnels": fonctionnels,
            "hors_service": hors_service,
            "en_reparation": en_reparation,
            "derniers": derniers,
            "categories": categories_raw,
            "installations_annee": installations_annee,
            "pct_annee_ecoule": pct_annee_ecoule,
            "garanties_dashboard": garanties_dashboard,
            "equipements": equipements,
            "consommables": consommables,
            "lieux": lieux,
            **contexte_securite
        }
    )

@app.exception_handler(Exception)
async def gestion_erreur_globale(request: Request, exc: Exception):
    user_id = request.session.get("user_id")
    email = "Anonyme"
    if user_id:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user:
                email = user.email

    logger.error(f"Erreur sur {request.url} - Utilisateur: {email} - Détail: {exc}")

    return templates.TemplateResponse(
        request=request,
        name="erreur.html",
        context={},
        status_code=500
    )