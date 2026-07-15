import os
import logging
from logging.handlers import RotatingFileHandler
from sqlmodel import Session, create_engine
from fastapi.templating import Jinja2Templates
from fastapi import Request, Depends
from app.models import User
from app.utils.consommables import (
    jours_ecouler_consommables,
    jours_restants_consommable,
    pourcentage_restant_consommable,
    statut_consommable,
    date_fin_estimee_consommable,
)

def get_current_user_for_templates(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"current_user": None, "can": lambda nom: False}
    with Session(engine) as session:
        user = session.get(User, user_id)
        return {
            "current_user": user,
            "can": lambda nom: user.has_perm(nom, session) if user else False
        }

#creation de mes fichiers de logs
os.makedirs("app/logs", exist_ok=True)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

file_handler = RotatingFileHandler(
    "app/logs/app.log",
    maxBytes=5242880,
    backupCount=5
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

#Création de ma database.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sqlite_file_name = os.path.join(BASE_DIR, "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

templates = Jinja2Templates(
    directory="app/templates",
    context_processors=[get_current_user_for_templates]
)
templates.env.globals["jours_ecouler_consommables"] = jours_ecouler_consommables
templates.env.globals["jours_restants_consommable"] = jours_restants_consommable
templates.env.globals["pourcentage_restant_consommable"] = pourcentage_restant_consommable
templates.env.globals["statut_consommable"] = statut_consommable
templates.env.globals["date_fin_estimee_consommable"] = date_fin_estimee_consommable

