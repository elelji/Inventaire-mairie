from sqlmodel import SQLModel, Field, create_engine, Relationship, select, Session
from typing import Optional
from datetime import date, datetime
from enum import Enum
#import sqlmodel

#table equipement
class Equipement(SQLModel, table=True):
   id: Optional[int] = Field(default=None, primary_key=True)
   nom: str
   lieu: str
   usager: Optional[str] = None
   categorie: str
   marque: str
   modele: str
   numero_serie: str = Field(unique=True)
   date_installation: Optional[date] = None
   etat: str
   salle: Optional[str] = None
   commentaire: Optional[str] = None
   version_os: Optional[str] = None
   cout: Optional[str] = None
   garanties: list["Garantie"] = Relationship(back_populates="equipement")
   consommables: list["Consommable"] = Relationship(back_populates="equipement")
   dans_corbeille: bool = Field(default=False)

#table garantie
class Garantie(SQLModel, table=True):
   id: Optional[int] = Field(default=None, primary_key=True)
   equipement_id: int = Field(default=None, foreign_key="equipement.id") #lien avec id des equipements
   date_debut: date
   duree_mois: int
   date_fin: date
   equipement: Optional["Equipement"] = Relationship(back_populates="garanties")

#table consommable
class Consommable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipement_id: Optional[int] = Field(default=None, foreign_key="equipement.id")
    type_consommable: str
    lieu: Optional[str] = None
    salle: Optional[str] = None
    date_installation: date
    duree_estimee_mois: int
    equipement: Optional["Equipement"] = Relationship(back_populates="consommables")
    remplace: bool = Field(default=False)

    
#table historique
class Historique(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipement_id: Optional[int] = Field(default=None, foreign_key="equipement.id") #lien avec id des equipements
    date_action: date
    action: str
    utilisateur: str
    commentaire: str 
    nom_equipement: str
    consommable_id: Optional[int] = Field(default=None, foreign_key="consommable.id") #lien avec id consommables

#types de rôles enum
class Role(str, Enum):
    administrateur = "administrateur"
    technicien = "technicien"
    utilisateur = "utilisateur"

#class utilisateur
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    mdp: str
    role: Role = Field(default=Role.utilisateur)
    status: bool = Field(default=True)
    code_2fa: Optional[str] = Field(default=None)
    code_2fa_expiration: Optional[datetime] = Field(default=None)
    doit_changer_mdp: bool = Field(default=True)
    tentatives_echouees: int = Field(default=0)
    bloque_jusqu_a: Optional[datetime] = Field(default=None)
    reset_token: Optional[str] = None
    reset_token_expiration: Optional[datetime] = None   
    totp_secret: Optional[str] = None
    totp_active: bool = Field(default=False)
    def has_perm(self, nom_permission: str, session: Session) -> bool:
        if self.role == Role.administrateur:
            return True
        if self.role == Role.utilisateur:
            return False
        stmt = select(Permission).where(Permission.nom == nom_permission)
        perm = session.exec(stmt).first()

        if perm is None:
            return False
            
        return perm.actif_pour_technicien

#class permission
class Permission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(unique=True)
    label: str
    actif_pour_technicien: bool = Field(default=False)

#class lieu
class Lieu(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(unique=True)

#class LOGCONNEXION
class LogConnexion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    date_action: datetime
    succes: bool
    ip : Optional[str] = None
