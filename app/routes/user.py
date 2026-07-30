from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from datetime import datetime
from app.dependencies import get_session, templates, logger
from app.models import User
from app.auth import require_permission, hash_password, get_current_user, generer_mdp_temporaire
from app.models import Role, LogConnexion
import smtplib

router = APIRouter()

@router.get("/admin/utilisateurs")
def voir_user(
    request: Request, 
    current_user: User = Depends(require_permission("voir_utilisateur")),
    session: Session = Depends(get_session)
):
    statement = select(User)
    user = session.exec(statement).all()
    return templates.TemplateResponse(
        request=request,
        name="user.html",
        context={"user": user, "roles": list(Role)}
    )

@router.get("/admin/utilisateurs/creer")
def create_user(
    request: Request,
    current_user: User = Depends(require_permission("creer_nouvel_utilisateur")),
    session: Session = Depends(get_session),
):
    return templates.TemplateResponse(            
        request=request,
        name="user.html",                         
        context={"roles": list(Role)}
    )

@router.post("/admin/utilisateurs/creer")
def create_user(
    request: Request,
    session: Session = Depends(get_session),
    current_user : User = Depends(require_permission("creer_nouvel_utilisateur")),
    email: str = Form(),
    role: str = Form(),
):
    if role == Role.administrateur.value and current_user.role != Role.administrateur:
        raise HTTPException(status_code=403, detail="Seul un administrateur peut créer un compte administrateur")
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=404, detail="Cet utilisateur est déjà enregistré")
    try:
        password = generer_mdp_temporaire(email)
    except smtplib.SMTPException as exc:
        logger.error(f"Échec d'envoi de l'email de bienvenue pour {email}: {exc}")
        raise HTTPException(status_code=503, detail="Le service d'envoi d'email est momentanément indisponible. Contactez l'administrateur système.")
    password_hash = hash_password(password)
    user = User(
        email=email,
        mdp = password_hash,
        role=role,
        doit_changer_mdp = True,
    )
    try:
        session.add(user)
        session.commit()
        logger.info('Un nouvel utilisateur est enregistré')
        return RedirectResponse(url="/admin/utilisateurs", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur d'enregistrement: {exc}")
    return templates.TemplateResponse(            
        request=request,
        name="user.html",                         
        context={}
    )

@router.post("/admin/utilisateurs/modifier/{user_id}")
def edit_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_permission("modifier_utilisateur")),
    session: Session = Depends(get_session),
    email: str = Form(),
    role: str = Form(),
):
    if role == Role.administrateur.value and current_user.role != Role.administrateur:
        raise HTTPException(status_code=403, detail="Seul un administrateur peut assigner le rôle administrateur")
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Cet utilisateur n'existe pas")
    try:
        user.email = email
        user.role = role
        session.add(user)
        session.commit()
        logger.info('Cet utilisateur a bien été modifié')
        return RedirectResponse(url="/admin/utilisateurs", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur de modification {exc}")

@router.post("/admin/utilisateurs/delete/{user_id}")
def delete_user(
    user_id: int,   
    request: Request,
    current_user: User = Depends(require_permission("supprimer_utilisateur")),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Cet user n'existe pas")
    try:
        session.delete(user)
        session.commit()
        logger.info('Utilisateur supprimés')
        return RedirectResponse(url="/admin/utilisateurs", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur de suppression {exc}")
        return HTMLResponse(content="L'equipement ne peut pas être supprimé", status_code=500)


@router.get("/admin/logs")
def voir_logs(
    request: Request,
    current_user: User = Depends(require_permission("consulter_logs_co")),
    session: Session = Depends(get_session),
):
    statement = (select(LogConnexion).order_by(LogConnexion.id.desc()))
    logs = session.exec(statement).all()
    return templates.TemplateResponse(
        request=request,
        name="logs_connexion.html",
        context={"logs": logs}
    )