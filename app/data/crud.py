from sqlalchemy.orm import Session, load_only
from sqlalchemy import extract, func
from typing import List
from random import sample
from datetime import datetime
from app.data import models, schemas
from app.auth.hash import hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first()

def get_hashed(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().hashed

def get_id(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().user_id

def get_profile(db: Session, id: str):
    return db.query(models.Profile).options(load_only(models.Profile.name, models.Profile.status, models.Profile.about, models.Profile.age)).get(id)

def create_profile(db: Session, profile: schemas.ProfileCreate) -> models.Profile:
    db_profile = models.Profile(name=profile.name, birth=profile.birth, sex=profile.sex)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def create_auth(db: Session, auth: schemas.AuthCreate, profile: schemas, id: str) -> models.Auth:
    db_auth = models.Auth(email=auth.email, hashed=hash(auth.password), user_id=profile.id, id=id, sent=datetime.today())
    db.add(db_auth)
    db.commit()
    db.refresh(db_auth)
    return db_auth

def change_auth_id(db: Session, email: str, id: str):
    old_id = db.query(models.Auth).filter(models.Auth.email == email).first().id
    db_auth = db.query(models.Auth).get(old_id)
    db_auth.id = id
    db.commit()

def change_auth_sent(db: Session, email: str, sent: datetime):
    old_id = db.query(models.Auth).filter(models.Auth.email == email).first().id
    db_auth = db.query(models.Auth).get(old_id)
    db_auth.sent = sent
    db.commit()

def change_name(db: Session, id: int, name: str):
    profile = db.query(models.Profile).get(id)
    profile.name = name
    db.commit()

def change_about(db: Session, id: int, about: str):
    profile = db.query(models.Profile).get(id)
    profile.about = about
    db.commit()

def change_status(db: Session, id: int, status: str):
    profile = db.query(models.Profile).get(id)
    profile.status = status
    db.commit()
    
def get_all_profiles(db: Session, id: int, agefrom: int, ageto: int) -> List[models.Profile]:
    result = db.query(models.Profile).filter(models.Profile.id != id, models.Profile.age >= agefrom, models.Profile.age <= ageto).options(load_only(models.Profile.name, models.Profile.status, models.Profile.age)).all()
    return result

def get_all_profiles_by_sex(db: Session, id: int, agefrom: int, ageto: int, sex: str) -> List[models.Profile]:
    result = db.query(models.Profile).filter(models.Profile.id != id, models.Profile.age >= agefrom, models.Profile.age <= ageto, models.Profile.sex == sex).options(load_only(models.Profile.name, models.Profile.status, models.Profile.age)).all()
    return result

def verify_auth(db: Session, id: str):
    db_auth = db.query(models.Auth).get(id)
    db_auth.verified = True
    db.commit()

def get_verified(db: Session, id: str):
    return db.query(models.Auth).filter(models.Auth.id == id).first().verified

def get_email_verified(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().verified

def get_auth(db: Session, id: str):
    return db.query(models.Auth).filter(models.Auth.id == id).first()

def get_email_sent(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().sent