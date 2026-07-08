from sqlmodel import Session
from app.dependencies import engine
from app.models import User, Role
from app.auth import hash_password

with Session(engine) as session:
    admin = User(
        email="ma.louisy@gmail.com",
        mdp=hash_password("change-moi"),
        role=Role.administrateur
    )
    session.add(admin)
    session.commit()
    print("Admin créé.")