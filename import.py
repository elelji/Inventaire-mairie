from app.dependencies import engine
from sqlmodel import Session
from app.utils.excel_parser import import_excel

with Session(engine) as session:
    import_excel("app/database/inventaire.xlsx", session)
    print("Import terminé")