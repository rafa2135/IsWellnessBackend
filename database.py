import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv() # cargar variables del .env

DATABASE_URL = os.getenv("DATABASE_URL") # tomando el string de la base de datos

ssla ={} # variables para ssl
capath="ca.pem" # ruta del certificado ssl
if os.path.exists(capath):
    ssla["ssl"] = {"ca":capath}

if not DATABASE_URL:    #validacion
    raise ValueError("DATABASE_URL .env no tiene una valor.")

engine = create_engine( # creando el engine para la base de datos 
    DATABASE_URL,
    echo=True,#ver query in la terminal
    connect_args=ssla
)

sessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine)

class Base(DeclarativeBase):# clase base para las tablas de la base de datos
    pass

def get_db(): # funcion para obtener el sesion local
    db= sessionLocal()
    try:
        yield db
    finally:
        db.close()