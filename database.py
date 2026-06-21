import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv() # cargar variables del .env

DATABASE_URL = os.getenv("DATABASE_URL") # tomando el string de la base de datos

if not DATABASE_URL:    #validacion
    raise ValueError("DATABASE_URL .env no tiene una valor.")

engine = create_engine(
    DATABASE_URL,
    echo=True,#ver query in la terminal
    connect_args={"ssl":{}}
)

sessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    db= sessionLocal()
    try:
        yield db
    finally:
        db.close()