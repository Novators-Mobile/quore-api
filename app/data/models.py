from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from app.data import database

class Profile(database.base):
    __tablename__ = 'profiles'

    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    birth = Column(Date(), CheckConstraint("birth < (current_date - interval '18' year )"), nullable=False)
    sex = Column(String(), nullable=False)
    about = Column(String(), nullable=True, default=None)
    auth = relationship("Auth")

class Auth(database.base):
    __tablename__ = 'auth'

    id = Column(String(), primary_key=True, unique=True)
    verified = Column(Boolean(), default=False, nullable=False)
    email = Column(String(), CheckConstraint("email LIKE '%@%.%'"), nullable=False, unique=True)
    hashed = Column(String(), nullable=False)   
    sent = Column(DateTime(), nullable=False, default=datetime.now)
    user_id = Column(Integer(), ForeignKey("profiles.id"))
    user = relationship("Profile")