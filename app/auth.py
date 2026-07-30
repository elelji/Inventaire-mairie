#AUTH.PY APP
import os 
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, Depends, HTTPException
from sqlmodel import Session, select
from app.dependencies import get_session
from app.models import User, Role, Permission
import smtplib
import random
from email.mime.text import MIMEText
import string
import secrets
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

SESSION_TIMEOUT_MINUTES = 30

def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    user_id = request.session.get("user_id")
    last_activity_str = request.session.get("last_activity")

    if not user_id or not last_activity_str:
        return None

    last_activity = datetime.fromisoformat(last_activity_str)
    if datetime.now() - last_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        request.session.pop("user_id", None) 
        request.session.pop("last_activity", None)
        return None

    request.session["last_activity"] = datetime.now().isoformat()
    return session.get(User, user_id)

def require_login(request: Request, user: Optional[User] = Depends(get_current_user)) -> User:
    if not user or not user.status:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if user.doit_changer_mdp:
        raise HTTPException(status_code=303, headers={"Location": "/changer-mdp"})
    if not user.totp_active and request.url.path not in ["/activer-2fa-app", "/activer-2fa-app/confirmer"]:
        raise HTTPException(status_code=303, headers={"Location": "/activer-2fa-app"})
    return user
    
def require_admin(user: User = Depends(require_login)) -> User:
    if user.role != Role.administrateur:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return user

def require_permission(nom_permission: str):
    def checker(
        current_user: User = Depends(require_login),
        session: Session = Depends(get_session)
    ) -> User:
        if current_user.role == Role.administrateur:
            return current_user

        if current_user.role == Role.utilisateur:
            # Stagiaire : consultation uniquement, jamais d'action
            raise HTTPException(status_code=403, detail="Accès en lecture seule")

        perm = session.exec(select(Permission).where(Permission.nom == nom_permission)).first()
        if not perm or not perm.actif_pour_technicien:
            raise HTTPException(status_code=403, detail="Permission refusée")
        return current_user
    return checker

#A2FA
#constantes de conf smtp
HOST: str = "smtp.gmail.com"
PORT: int = 587
EMAIL: str = os.getenv('EMAIL_DSI')
MOT_DE_PASSE: str = os.getenv('EMAIL_DSI_MOT_DE_PASSE')

APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")

def envoyer_url(destinataire: str) -> str:
    token = secrets.token_urlsafe(32)
    #construction de l'email
    msg = MIMEText(f"Voici le lien vous permettant de modifier votre mot de passe : {APP_BASE_URL}/reset-mdp/{token}")
    msg["Subject"] = "Mot de passe oublié — Inventaire DSI"
    msg["From"] = EMAIL
    msg["To"] = destinataire
    #evoie du message
    with smtplib.SMTP(HOST,PORT) as server:
        server.starttls()
        server.login(EMAIL, MOT_DE_PASSE)
        server.sendmail(EMAIL, destinataire, msg.as_string())
    return token 

#fonction d'envoie code 2fa
def envoyer_code_2fa(destinataire: str) -> str:
    #code 6 chiffre générer
    code = str(random.randint(100000, 999999))
    #construction de l'email
    msg = MIMEText(f"Voici votre code de connexion {code}")
    msg["Subject"] = "Code de connexion — Inventaire DSI"
    msg["From"] = EMAIL
    msg["To"] = destinataire
    #evoie du message
    with smtplib.SMTP(HOST,PORT) as server:
        server.starttls()
        server.login(EMAIL, MOT_DE_PASSE)
        server.sendmail(EMAIL, destinataire, msg.as_string())
    return code 

def generer_mdp_temporaire(destinataire: str) -> str:
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(10))
    msg = MIMEText(f"Voici votre code de connexion {password}")
    msg["Subject"] = "Mot de passe — Inventaire DSI"
    msg["From"] = EMAIL
    msg["To"] = destinataire
    #evoie du message
    with smtplib.SMTP(HOST,PORT) as server:
        server.starttls()
        server.login(EMAIL, MOT_DE_PASSE)
        server.sendmail(EMAIL, destinataire, msg.as_string())
    return password

