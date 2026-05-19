from fastapi import Depends, HTTPException, status, Header
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings

def obter_db():
    """Injeção de dependência modular da sessão SQL"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verificar_rbac(papeis_permitidos: list):
    """Controle de Acesso Baseado em Funções (RBAC) modularizado"""
    def validador(authorization: str = Header(...), db: Session = Depends(obter_db)):
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Esquema de autenticação inválido.")
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if not username or not role:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token corrompido.")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado ou inválido.")
            
        if role not in papeis_permitidos:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado para a sua função.")
        return {"username": username, "role": role}
    return validador