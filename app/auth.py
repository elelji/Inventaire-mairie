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
PORT: int = 465
EMAIL: str = os.getenv('EMAIL_DSI')
MOT_DE_PASSE: str = os.getenv('EMAIL_DSI_MOT_DE_PASSE')
BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost")

def envoyer_url(destinataire: str) -> str:
    token = secrets.token_urlsafe(32)
    #construction de l'email
    lien = f"{BASE_URL}/reset-mdp/{token}"
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                
                <h2 style="color: #4338CA;">
                    Inventaire DSI - Réinitialisation du mot de passe
                </h2>

                <p>Bonjour,</p>

                <p>
                    Une demande de réinitialisation de votre mot de passe a été effectuée.
                </p>

                <p>
                    Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe :
                </p>

                <div style="text-align: center; margin: 30px;">
                    <a href="{lien}" 
                       style="background-color: #4338CA; color: white; 
                       padding: 12px 20px; text-decoration: none; 
                       border-radius: 5px;">
                        Réinitialiser mon mot de passe
                    </a>
                </div>

                <p>
                    Ce lien est valable pendant <b>30 minutes</b>.
                </p>

                <p>
                    Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email.
                </p>

                <hr>

                <p style="font-size: 12px; color: #777;">
                    Message automatique envoyé par l'application Inventaire DSI.
                </p>

            </div>
        </body>
    </html>
    """
    msg = MIMEText(html, "html")
    msg["Subject"] = "Mot de passe oublié — Inventaire DSI"
    msg["From"] = EMAIL
    msg["To"] = destinataire
    #evoie du message
    with smtplib.SMTP_SSL(HOST,PORT) as server:
        server.login(EMAIL, MOT_DE_PASSE)
        server.sendmail(EMAIL, destinataire, msg.as_string())
    return token 

#fonction d'envoie code 2fa
def envoyer_code_2fa(destinataire: str) -> str:
    #code 6 chiffre générer
    code = str(random.randint(100000, 999999))
    #construction de l'email
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">

                <h2 style="color: #4338CA;">
                    Inventaire DSI - Code de connexion
                </h2>

                <p>Bonjour,</p>

                <p>
                    Une tentative de connexion nécessite une vérification supplémentaire.
                </p>

                <p>
                    Voici votre code de sécurité :
                </p>

                <div style="
                    text-align: center;
                    margin: 30px;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #4338CA;
                ">
                    {code}
                </div>

                <p>
                    Ce code est valable pendant quelques minutes.
                </p>

                <p>
                    Si vous n'êtes pas à l'origine de cette connexion, 
                    veuillez contacter l'administrateur.
                </p>

                <hr>

                <p style="font-size: 12px; color: #777;">
                    Message automatique envoyé par l'application Inventaire DSI.
                </p>

            </div>
        </body>
    </html>
    """
    msg = MIMEText(html, "html")
    msg["Subject"] = "Code de connexion — Inventaire DSI"
    msg["From"] = EMAIL
    msg["To"] = destinataire
    #evoie du message
    with smtplib.SMTP_SSL(HOST,PORT) as server:
        server.login(EMAIL, MOT_DE_PASSE)
        server.sendmail(EMAIL, destinataire, msg.as_string())
    return code 

def generer_mdp_temporaire(destinataire: str) -> str:
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(10))
    #construction message
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">

                <h2 style="color: #4338CA;">
                    Inventaire DSI - Code de connexion temporaire
                </h2>

                <p>Bonjour,</p>

                <p>
                    Un mot de passe temporaire a été généré pour votre compte.
                </p>

                <p>
                    Utilisez le mot de passe suivant pour vous connecter :
                </p>

                <div style="
                    text-align: center;
                    margin: 30px;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #4338CA;
                ">
                    {password}
                </div>

                <p>
                    Vous devrez obligatoirement modifier ce mot de passe lors de votre prochaine connexion
                </p>

                <p>
                    Si vous n'êtes pas à l'origine de cette connexion, 
                    veuillez contacter l'administrateur.
                </p>

                <hr>

                <p style="font-size: 12px; color: #777;">
                    Message automatique envoyé par l'application Inventaire DSI.
                </p>

            </div>
        </body>
    </html>
    """    
    msg = MIMEText(html, "html")
    msg["Subject"] = "Mot de passe temporaire — Inventaire DSI"
    msg["From"] = EMAIL
    msg["To"] = destinataire
    #evoie du message
    with smtplib.SMTP_SSL(HOST,PORT) as server:
        server.login(EMAIL, MOT_DE_PASSE)
        server.sendmail(EMAIL, destinataire, msg.as_string())
    return password

