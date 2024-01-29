from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, CheckConstraint, DateTime, extract, func
from sqlalchemy.orm import relationship, column_property
import datetime
from app.data import database

class Profile(database.base):
    __tablename__ = 'profiles'

    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    birth = Column(Date(), nullable=False)
    age = column_property(extract('year', func.age(birth)))
    sex = Column(String(), nullable=False)
    about = Column(String(), nullable=True, default="")
    status = Column(String(), nullable=True, default="")
    auth = relationship("Auth")

class Auth(database.base):
    __tablename__ = 'auth'

    id = Column(String(), primary_key=True, unique=True)
    verified = Column(Boolean(), default=False, nullable=False)
    email = Column(String(), CheckConstraint("email LIKE '%@%.%'"), nullable=False, unique=True)
    hashed = Column(String(), nullable=False)   
    sent = Column(DateTime(), nullable=False, default=datetime.datetime.now)
    user_id = Column(Integer(), ForeignKey("profiles.id"))
    user = relationship("Profile")

class Like(database.base):
    __tablename__ = 'likes'

    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    initiator = Column(Integer(), ForeignKey('profiles.id'))
    target = Column(Integer(), ForeignKey('profiles.id'))
    match = Column(Boolean(), default=False)
    created = Column(DateTime(), nullable=False, default=datetime.datetime.now)

class Dislike(database.base):
    __tablename__ = "dislikes"

    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    initiator = Column(Integer(), ForeignKey('profiles.id'))
    target = Column(Integer(), ForeignKey('profiles.id'))
    created = Column(DateTime(), nullable=False, default=datetime.datetime.now)