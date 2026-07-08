#AUTH.PY APP/ROUTE
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.dependencies import get_session, templates, logger
from app.models import User
from app.auth import verify_password, envoyer_code_2fa, require_permission, generer_mdp_temporaire, hash_password, require_login, get_current_user, envoyer_url
from app.models import Role, LogConnexion
from typing import Optional
import secrets

router = APIRouter()

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == email)).first()
    if user and user.bloque_jusqu_a and datetime.now() < user.bloque_jusqu_a:
        log = LogConnexion(
            email=email, 
            succes=False, 
            ip=request.client.host,
            date_action=datetime.now()
            )
        session.add(log)
        session.commit()
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"erreur": "Compte temporairement bloqué, réessayez plus tard"}
        )
    if not user:
        log = LogConnexion(
            email=email, 
            succes=False, 
            ip=request.client.host,
            date_action=datetime.now()
            )
        session.add(log)
        session.commit()
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"erreur": "Email incorrect"}
        )
    if not verify_password(password, user.mdp):
        user.tentatives_echouees += 1
        if user.tentatives_echouees >= 5:
            user.bloque_jusqu_a = datetime.now() + timedelta(minutes=15)
            session.add(user)
            session.commit()
            log = LogConnexion(
                email=email, 
                succes=False, 
                ip=request.client.host,
                date_action=datetime.now()
                )
            session.add(log)
            session.commit()
            return templates.TemplateResponse(
                request=request, name="login.html",
                context={"erreur": "Compte temporairement bloqué, réessayez plus tard"}
            )
        session.add(user)
        session.commit()
        log = LogConnexion(
                email=email, 
                succes=False, 
                ip=request.client.host,
                date_action=datetime.now()
                )
        session.add(log)
        session.commit()
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"erreur": "Email ou mot de passe incorrect"}
    )
    if verify_password(password, user.mdp):
        user.tentatives_echouees = 0
        user.bloque_jusqu_a = None
        session.add(user)
        session.commit()
    deux_fa_valide = request.session.get("deux_fa_valide_jusqu_a")
    if deux_fa_valide and datetime.fromisoformat(deux_fa_valide) > datetime.now():
        request.session["user_id"] = user.id
        request.session["last_activity"] = datetime.now().isoformat()
        return RedirectResponse(url="/", status_code=303)
    code = envoyer_code_2fa(user.email)
    user.code_2fa = code
    user.code_2fa_expiration = datetime.now() + timedelta(minutes=10)
    session.add(user)
    session.commit()
    log = LogConnexion(
            email=email, 
            succes=True, 
            ip=request.client.host,
            date_action=datetime.now()
            )
    session.add(log)
    session.commit()
    request.session["pending_user_id"] = user.id
    return RedirectResponse(url="/verify-2fa", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/verify-2fa/renvoyer")
def renvoyer_2fa(request: Request, session: Session = Depends(get_session)):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    code = envoyer_code_2fa(user.email)
    user.code_2fa = code
    user.code_2fa_expiration = datetime.now() + timedelta(minutes=10)
    session.add(user)
    session.commit()
    return RedirectResponse(url="/verify-2fa", status_code=303)



@router.get("/verify-2fa")
def verify_2fa(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="verify_2fa.html",
        context={}
    )

@router.post("/verify-2fa")
def verify_2fa(request: Request, session: Session = Depends(get_session), code: str = Form()):
    user_id = request.session.get("pending_user_id")
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user_id or not user:
        return RedirectResponse(url="/login", status_code=303)
    if code != user.code_2fa or datetime.now() > user.code_2fa_expiration:
        return templates.TemplateResponse(
            request=request,
            name="verify_2fa.html",
            context={"erreur": "Code invalide ou expiré"}
        )
    print(f"SESSION APRES LOGIN : {dict(request.session)}")
    del request.session["pending_user_id"]
    request.session["user_id"] = user.id
    request.session["deux_fa_valide_jusqu_a"] = (datetime.now() + timedelta(hours=8)).isoformat()
    request.session["last_activity"] = datetime.now().isoformat()
    return RedirectResponse(url="/", status_code=303)

@router.get("/changer-mdp")
def changer_mdp_form(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="changer_mdp.html", context={})

@router.post("/changer-mdp")
def changer_mdp(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
    ancien_mdp: str = Form(),
    nouveau_mdp: str = Form(),
    confirmation_mdp: str = Form(),
):
    if nouveau_mdp != confirmation_mdp:
        return templates.TemplateResponse(request=request, name="changer_mdp.html", context={"erreur": "Les mots de passe ne correspondent pas"})
    if not verify_password(ancien_mdp, current_user.mdp):
        return templates.TemplateResponse(
            request=request, name="changer_mdp.html",
            context={"erreur": "Ancien mot de passe incorrect"}
        )
    if nouveau_mdp != len(nouveau_mdp) < 8:
        return templates.TemplateResponse(
            request=request, name="changer_mdp.html",
            context={"erreur": "Le mot de passe doit contenir au moins 8 caractères"}
        )
    password_hash = hash_password(nouveau_mdp)
    current_user.mdp = password_hash
    current_user.doit_changer_mdp = False
    try:
        session.add(current_user)
        session.commit()
        return RedirectResponse(url="/", status_code=303)
    except Exception as exc:
        logger.error(f"Erreur de modification {exc}")
        return HTMLResponse(content="Le nouveau mot de passe ne peut pas être créer", status_code=500)

@router.get("/reset_mdp")
def reset_mdp(request: Request):
    return templates.TemplateResponse(request=request, name="reset_mdp.html", context={})

@router.post("/reset-mdp")
def reset_mdp(request: Request, session: Session = Depends(get_session), email: str=Form()):
    user= session.exec((select(User).where(User.email == email))).first()
    if not user:
        return templates.TemplateResponse(
            request=request, name="reset_mdp.html",
            context={"succès":"Si cet email existe, un lien vous a été envoyé"}
        )
    token = envoyer_url(user.email)
    user.reset_token = token
    user.reset_token_expiration = datetime.now() + timedelta(minutes=30)
    session.add(user)
    session.commit()
    return templates.TemplateResponse(request=request, name="reset_mdp.html", context={"succès": "Si cet email existe, un lien vous a été envoyé"})

@router.get("/reset-mdp/{token}")
def reset_mdp_form(token : str, request: Request, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.reset_token == token)).first()
    if not user:
        return templates.TemplateResponse(request=request, name="reset_mdp.html", context={"erreur": "Veuillez réessayer"})
    if datetime.now() > user.reset_token_expiration:
        return templates.TemplateResponse(request=request, name="reset_mdp.html", context={"erreur": "Veuillez réessayer"})
    else: 
        return templates.TemplateResponse(request=request, name="reset_mdp_confirm.html", context={"token": token})

@router.post("/reset-mdp/{token}")
def reset_mdp_form(token : str, request: Request, session: Session = Depends(get_session), nouveau_mdp : str = Form()):
    user = session.exec(select(User).where(User.reset_token == token)).first()
    if not user:
        return templates.TemplateResponse(request=request, name="reset_mdp.html", context={"erreur": "Veuillez réessayer"})
    if datetime.now() > user.reset_token_expiration:
        return templates.TemplateResponse(request=request, name="reset_mdp.html", context={"erreur": "Veuillez réessayer"})
    user.mdp = hash_password(nouveau_mdp)
    user.reset_token = None
    user.reset_token_expiration = None
    session.add(user)
    session.commit()
    return RedirectResponse(url="/login", status_code=303)

