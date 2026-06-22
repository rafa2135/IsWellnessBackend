from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, engine, Base
import models
from routers.auth import router as auth_router

app = FastAPI(title="API Wellness")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"status": "El servidor esta corriendo"}


@app.get("/test-db")
def test_db_con(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"message": "Conexion a Aiven exitosa", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error de conexion: {str(e)}"
        )

