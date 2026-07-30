from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import List
from app.dependencies import get_session, templates
from app.auth import require_admin
from app.models import Permission, User

router = APIRouter(prefix="/admin")

@router.get("/permissions")
def voir_permissions(request: Request, current_user: User = Depends(require_admin), session: Session = Depends(get_session)):
    permissions = session.exec(select(Permission)).all()
    return templates.TemplateResponse(
        request=request, name="admin_permissions.html",
        context={"permissions": permissions}
    )

@router.post("/permissions")
async def modifier_permissions(request: Request, current_user: User = Depends(require_admin), session: Session = Depends(get_session)):
    form = await request.form()
    noms_actives = form.getlist("permission")  # noms des permissions cochées

    permissions = session.exec(select(Permission)).all()
    for perm in permissions:
        perm.actif_pour_technicien = perm.nom in noms_actives
        session.add(perm)
    session.commit()

    return RedirectResponse(url="/admin/permissions", status_code=303)