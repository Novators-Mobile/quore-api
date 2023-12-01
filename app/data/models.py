from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, backref
from app.data import database

class Profile(database.base):
    __tablename__ = 'profiles'

    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    birth = Column(Date(), nullable=False)
    sex = Column(String(), nullable=False)

    auth = relationship("Auth")

class Auth(database.base):
    __tablename__ = 'auth'

    email = Column(String(), CheckConstraint("email LIKE '%@%.%'"), nullable=False, unique=True)
    hashed = Column(String(), nullable=False)   
    user_id = Column(Integer(), ForeignKey("profiles.id"), primary_key=True)
    user = relationship("Profile")

