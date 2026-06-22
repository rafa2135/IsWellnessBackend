import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import get_db
from models import User

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no configurada en .env")

ALGORITHM = "HS256" # algoritmo de encriptación
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) # expiración del token

pwd_hash = PasswordHash.recommended() # algoritmo de hashing

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # url para el login


def hash_password(plain: str) -> str: # hashing de contraseñas
    return pwd_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool: # verificación de contraseñas
    return pwd_hash.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str: # creación del token
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user( # obtención del usuario actual
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:# checkeo del token para verificación
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: falta subject",
            )
    except InvalidTokenError: # si el token es invalido o expirado, se lanza una excepción
        raise HTTPException(# se lanza una excepción con un código de estado 401 y un mensaje
            status_code=status.HTTP_401_UNAUTHORIZED,#error 401 = unauthorized (no autorizado)
            detail="Token invalido o expirado",
        )

    user = db.query(User).filter(User.id == user_id).first() # se busca el usuario en la base de datos con el id del token
    if user is None: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user
