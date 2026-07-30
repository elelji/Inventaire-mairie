import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.dependencies import engine
from app.models import Equipement, Lieu

if __name__ == "__main__":
    with Session(engine) as session:
        lieux_existants = session.exec(select(Equipement.lieu).distinct()).all()
        for nom in lieux_existants:
            if not nom:
                continue
            existing = session.exec(select(Lieu).where(Lieu.nom == nom)).first()
            if not existing:
                session.add(Lieu(nom=nom))
        session.commit()
        print("Lieux migrés.")