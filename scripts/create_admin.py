import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session
from app.dependencies import engine
from app.models import User, Role
from app.auth import hash_password
import getpass

email = input("Email de l'administrateur : ")
mot_de_passe = getpass.getpass("Mot de passe initial : ")

with Session(engine) as session:
    admin = User(
        email=email,
        mdp=hash_password(mot_de_passe),
        role=Role.administrateur
    )
    session.add(admin)
    session.commit()

print("Admin créé.")
