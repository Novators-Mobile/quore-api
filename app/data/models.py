from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship

engine = create_engine("")
Base = declarative_base()

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer(), primary_key=True, unique=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    birth = Column(Date(), nullable=False)
    sex = Column(String(), nullable=False)
    auth = relationship("Auth", backref="user")

class Auth(Base):
    __tablename__ = 'auth'
    email = Column(String(), CheckConstraint("email LIKE '%@%.%'"), nullable=False, unique=True)
    hashed = Column(String(), nullable=False)
    user_id = Column(ForeignKey("profiles.id"), primary_key=True)

Base.metadata.create_all(engine)