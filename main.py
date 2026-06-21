from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine, Base

app = FastAPI(title="API")

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"status":"El servidor esta corriendo"}

@app.get("/test-db")
def test_db_con(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"message": "Conexion a Aiven exitosa", "result":result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errir de conexion: {str(e)}")

