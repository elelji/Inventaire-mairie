from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.models import User
from app.dependencies import templates, get_session, engine, logger
from app.auth import require_permission, require_login


router = APIRouter()

# Test projet ManageEngine
@router.get("/manageengine", response_class=HTMLResponse)
async def manageengine_page(request: Request, current_user: User = Depends(require_login)):
    return templates.TemplateResponse(
        request=request,
        name="manageengine.html",
        context={}
    )

@router.post("/manageengine/sync")
async def manageengine_sync(
    request: Request,
    session: Session = Depends(get_session),
    me_url: str = Form(),
    me_apikey: str = Form(),
):
    try:
        import requests as req
        # Test de connexion
        response = req.get(
            f"{me_url}/api/v3/assets",
            headers={"authtoken": me_apikey},
            timeout=5,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            assets = data.get("assets", [])
            return templates.TemplateResponse(
                request=request,
                name="manageengine.html",
                context={
                    "succes": True,
                    "nb_assets": len(assets),
                    "me_url": me_url,
                    "me_apikey": me_apikey,
                }
            )

        else:
            return templates.TemplateResponse(
                request=request,
                name="manageengine.html",
                context={
                    "erreur": f"Connexion échouée — code {response.status_code}",
                    "me_url": me_url,
                    "me_apikey": me_apikey,
                }
            )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="manageengine.html",
            context={
                "erreur": f"Impossible de joindre le serveur : {str(e)}",
                "me_url": me_url,
                "me_apikey": me_apikey,
            }
        )