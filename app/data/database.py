from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from os import environ

engine = create_engine(environ["DB_SERVER"])
Base = declarative_base()

Base.metadata.create_all(engine)