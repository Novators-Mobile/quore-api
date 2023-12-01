from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from os import environ

engine = create_engine(environ["DB_SERVER"])
base = declarative_base()
session = sessionmaker(engine)