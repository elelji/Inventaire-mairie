from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, Response, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models import Equipement, User, Lieu, Historique
from datetime import date
from sqlmodel import Session, select, func
from typing import Optional
from app.dependencies import templates, get_session, engine, logger
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import date
from docx import Document
from app.auth import require_permission, require_login
from weasyprint import HTML as WeasyprintHTML
from collections import defaultdict

router = APIRouter()

#GET /export - afficher page d'export
@router.get("/export_page", response_class=HTMLResponse)
async def export_page(request: Request, current_user: User = Depends(require_login),session: Session = Depends(get_session)):
    lieux = session.exec(select(Lieu.nom, func.count(Equipement.id)).join(Equipement, Equipement.lieu == Lieu.nom, isouter=True).group_by(Lieu.nom)).all()
    categories = session.exec(select(Equipement.categorie, func.count(Equipement.id)).group_by(Equipement.categorie)).all()
    marques = session.exec(select(Equipement.marque, func.count(Equipement.id)).group_by(Equipement.marque)).all()
    etats = ["Fonctionnel", "Hors service", "En réparation"]
    salles = session.exec(select(Equipement.salle, func.count(Equipement.id)).group_by(Equipement.salle)).all()
    
    return templates.TemplateResponse(
        request=request,
        name="export.html",
        context={
            "lieux": lieux,
            "categories": categories,
            "marques": marques,
            "etats": etats,
            "salles": salles,
        }
    )

#GET / TRI SALLES
@router.get("/api/salles")
async def get_salles(lieux: list[str] = Query(default=[]), session: Session = Depends(get_session)):
    query = select(Equipement.salle, func.count(Equipement.id)).group_by(Equipement.salle)
    if lieux:
        query = query.where(Equipement.lieu.in_(lieux))
    result = session.exec(query).all()
    return JSONResponse([{"salle": s, "total": t} for s, t in result if s])

#GET / TRI CATÉGORIES
@router.get("/api/categorie")
async def get_cat(
    lieux: list[str] = Query(default=[]),
    salles: list[str] = Query(default=[]),
    session: Session = Depends(get_session)
):
    query = select(Equipement.categorie, func.count(Equipement.id)).group_by(Equipement.categorie)
    if lieux:
        query = query.where(Equipement.lieu.in_(lieux))
    if salles:
        query = query.where(Equipement.salle.in_(salles))
    result = session.exec(query).all()
    return JSONResponse([{"categorie": s, "total": t} for s, t in result if s])

#GET / TRI MARQUES
@router.get("/api/marque")
async def get_marque(
    lieux: list[str] = Query(default=[]),
    salles: list[str] = Query(default=[]),
    categories: list[str] = Query(default=[]),
    session: Session = Depends(get_session)
):
    query = select(Equipement.marque, func.count(Equipement.id)).group_by(Equipement.marque)
    if lieux:
        query = query.where(Equipement.lieu.in_(lieux))
    if salles:
        query = query.where(Equipement.salle.in_(salles))
    if categories:
        query = query.where(Equipement.categorie.in_(categories))
    result = session.exec(query).all()
    return JSONResponse([{"marque": s, "total": t} for s, t in result if s])

#POST /EXPORT -EXCEL - génerer l'export
@router.post("/export_excel")
async def export(
    request: Request, 
    current_user: User = Depends(require_permission("generer_pdf")), 
    session: Session = Depends(get_session),
    lieux: list[str] = Form(default=[]),
    categories: list[str] = Form(default=[]),
    marques: list[str] = Form(default=[]),
    etats: list[str] = Form(default=[]),
    salles: list[str] = Form(default=[]),
    date_debut: date = Form(default=None),
    date_fin: date = Form(default=None),
):
    query = select(Equipement)
    if lieux:
        query = query.where(Equipement.lieu.in_(lieux))
    if categories:
        query = query.where(Equipement.categorie.in_(categories))
    if marques:
        query = query.where(Equipement.marque.in_(marques))
    if etats:
        query = query.where(Equipement.etat.in_(etats))
    if salles:
        query = query.where(Equipement.salle.in_(salles))
    if date_debut:
        query = query.where(Equipement.date_installation >= (date_debut))
    if date_fin:
        query = query.where(Equipement.date_installation <= (date_fin))   

    equipements = session.exec(query).all()

    # 1. Création du classeur Excel en mémoire
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventaire Parc"
    # --- CONFIGURATION DES STYLES ---
    # Couleurs de ta charte graphique
    bleu_fonce_dsi = "1A3A5C"
    bleu_clair_zebra = "F8FAFC"
    texte_blanc = "FFFFFF"
    
    # Polices et Remplissages
    font_header = Font(name="Segoe UI", size=11, bold=True, color=texte_blanc)
    font_data = Font(name="Segoe UI", size=10)
    
    fill_header = PatternFill(start_color=bleu_fonce_dsi, end_color=bleu_fonce_dsi, fill_type="solid")
    fill_zebra = PatternFill(start_color=bleu_clair_zebra, end_color=bleu_clair_zebra, fill_type="solid")
    
    # Bordures fines et discrètes
    bd_fine = Side(style="thin", color="E2E8F0")
    border_data = Border(left=bd_fine, right=bd_fine, top=bd_fine, bottom=bd_fine)
    
    # Alignements
    align_left = Alignment(horizontal="left", vertical="center")
    align_center = Alignment(horizontal="center", vertical="center")

    # 3. Ajout des en-têtes (Ligne 1)
    headers = ["Nom", "Lieu", "Salle", "Catégorie", "Marque", "Modèle", "N° Série", "État", "Date d'installation"]
    ws.append(headers)
    
    # Style de la ligne d'en-tête
    ws.row_dimensions[1].height = 26  # Plus haute pour respirer
    for cell in ws[1]:
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    # 4. Remplissage des données
    for index, e in enumerate(equipements, start=2): # start=2 car la ligne 1 est l'en-tête
        date_formatee = e.date_installation.strftime("%d/%m/%Y") if e.date_installation else ""
        
        ws.append([
            e.nom or "",
            e.lieu or "",
            e.salle or "",
            e.categorie or "",
            e.marque or "",
            e.modele or "",
            e.numero_serie or "",
            e.etat or "",
            date_formatee
        ])
        
        # Style de la ligne de données courante
        ws.row_dimensions[index].height = 20  # Lignes plus spacieuses
        for cell in ws[index]:
            cell.font = font_data
            cell.border = border_data
            
            # Aligner la date au centre, le reste à gauche
            if cell.column == 9:  # 9ème colonne = Date d'installation
                cell.alignment = align_center
            else:
                cell.alignment = align_left
                
            # Effet zèbre (une ligne sur deux légèrement grisée)
            if index % 2 == 0:
                cell.fill = fill_zebra

    # --- AJUSTEMENT AUTOMATIQUE DES COLONNES ---
    # Pour éviter que le texte soit coupé ou affiche des "###"
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter  # Récupère la lettre (A, B, C...)
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        # On ajuste la largeur avec une petite marge de sécurité de 4 caractères
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # 5. Sauvegarde et envoi du fichier
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    filename = f"inventaire_DSI_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

#POST /export - générer l'export
@router.post("/export")
async def expord(
    request: Request,
    current_user: User = Depends(require_permission("generer_pdf")),
    session: Session = Depends(get_session),
    lieux: list[str] = Form(default=[]),
    categories: list[str] = Form(default=[]),
    marques: list[str] = Form(default=[]),
    etats: list[str] = Form(default=[]),
    salles: list[str] = Form(default=[]),
    date_debut: date = Form(default=None),
    date_fin: date = Form(default=None),
):
    query = select(Equipement)
    if lieux:
        query = query.where(Equipement.lieu.in_(lieux))
    if categories:
        query = query.where(Equipement.categorie.in_(categories))
    if marques:
        query = query.where(Equipement.marque.in_(marques))
    if etats:
        query = query.where(Equipement.etat.in_(etats))
    if salles:
        query = query.where(Equipement.salle.in_(salles))
    if date_debut:
        query = query.where(Equipement.date_installation >= (date_debut))
    if date_fin:
        query = query.where(Equipement.date_installation <= (date_fin))   

    equipements = session.exec(query).all()
    
    equipements_par_lieu = defaultdict(list)
    for e in equipements:
        equipements_par_lieu[e.lieu].append(e)

    total = len(equipements)
    fonctionnels = sum(1 for e in equipements if e.etat == "fonctionnel")
    hors_service = sum(1 for e in equipements if e.etat == "hors service")
    en_reparation = sum(1 for e in equipements if e.etat == "en réparation")

    # Phrase intro
    parties = []
    if categories:
        parties.append(f"de catégorie {', '.join(categories)}")
    if lieux:
        parties.append(f"situés à {', '.join(lieux)}")
    if salles:
        parties.append(f"en salle {', '.join(salles)}")
    if etats:
        parties.append(f"en état {', '.join(etats)}")
    if marques:
        parties.append(f"de marque {', '.join(marques)}")

    if parties:
        intro = "Voici un compte rendu des équipements " + ", ".join(parties) + "."
    else:
        intro = "Voici un compte rendu de l'ensemble du parc informatique."

    try:

        html_str = templates.get_template("export_pdf.html").render(
            equipements_par_lieu=equipements_par_lieu,
            total=total,
            fonctionnels=fonctionnels,
            hors_service=hors_service,
            en_reparation=en_reparation,
            intro=intro,
            date_generation=date.today().strftime("%d/%m/%Y"),
            date_debut=date_debut,
            date_fin=date_fin,
        )
        # Générer le PDF
        pdf_bytes = WeasyprintHTML(string=html_str).write_pdf()
        filename = f"inventaire_DSI_{date.today().strftime('%Y%m%d')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        print(f"ERREUR PDF : {e}")
        return Response(content=str(e), media_type="text/plain")

#Export sortie d'inventaire
@router.get("/sortie_inventaire", response_class=HTMLResponse)
async def sortie_inventaire_form(
    request: Request,
    current_user : User = Depends(require_login),
    session: Session = Depends(get_session),
):
    lieux = session.exec(select(Lieu.nom)).all()
    categories = session.exec(select(Equipement.categorie, func.count(Equipement.id)).group_by(Equipement.categorie)).all()
    return templates.TemplateResponse(
        request=request,
        name="sortie_inventaire.html",
        context={
            "lieux":lieux,
            "categories": categories,
        }
    )

@router.post("/sortie_inventaire/pdf")
async def sortie_inventaire(
    request: Request,
    current_user : User = Depends(require_permission("generer_sortie_inventaire")),
    session: Session = Depends(get_session),
    lieux: list[str] = Form(default=[]),
    categories: list[str] = Form(default=[]),
    date_debut: date = Form(default=None),
    date_fin: date = Form(default=None),
):
    statement = (
        select(Historique, Equipement)
        .join(Equipement, Historique.equipement_id == Equipement.id, isouter=True)
        .where(Equipement.dans_corbeille == True).where(Historique.action == str("Suppression"))
        .order_by(Historique.id.desc())
    )
    if date_debut:
        statement = statement.where(Historique.date_action >= (date_debut))
    if date_fin:
        statement = statement.where(Historique.date_action <= (date_fin))   
    if lieux:
        statement = statement.where(Equipement.lieu.in_(lieux))
    if categories:
        statement = statement.where(Equipement.categorie.in_(categories))

    result = session.exec(statement).all()
    equipements_sortie = [
    {
        "equipement": equipement,
        "date_suppression": historique.date_action,
        "commentaire": historique.commentaire,
    }
    for historique, equipement in result
]
    try:
        context = {
            "equipements": equipements_sortie,
            "total": len(equipements_sortie),
            "date_debut": date_debut,
            "date_fin": date_fin,
            "date_generation": date.today().strftime("%d/%m/%Y"),
        }

        html_str = templates.get_template("sortie_inventaire_pdf.html").render(
            equipements=equipements_sortie,
            total=len(equipements_sortie),
            date_debut=date_debut,
            date_fin=date_fin,
            date_generation=date.today().strftime("%d/%m/%Y"),
)
        pdf_bytes = WeasyprintHTML(string=html_str).write_pdf()
        filename = f"sortie_inventaire_DSI_{date.today().strftime('%Y%m%d')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        print(f"ERREUR PDF : {e}")
        return Response(content=str(e), media_type="text/plain")
