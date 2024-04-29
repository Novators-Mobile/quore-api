from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey, CheckConstraint, DateTime, extract, func, ARRAY
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
    about = Column(String(), nullable=True, default=None)
    status = Column(String(), nullable=True, default=None)
    avatar = Column(Boolean(), default=False)
    images = Column(ARRAY(String), default=[])
    uploaded = Column(Integer(), nullable=True, default=0)
    preferences = Column(String(), nullable=True, default=None)
    latitude = Column(Float(), nullable=True, default=None)
    longitude = Column(Float(), nullable=True, default=None)
    fcm_token = Column(String(), nullable=False)
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

class Messages(database.base):
    __tablename__ = "messages"

    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    sender = Column(Integer(), ForeignKey('profiles.id'))
    recipient = Column(Integer(), ForeignKey('profiles.id'))
    sent = Column(DateTime(), nullable=False, default=datetime.datetime.now)
    message = Column(String(), nullable=True)
    attachments = Column(ARRAY(String), default=[])