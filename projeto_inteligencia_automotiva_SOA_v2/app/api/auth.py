from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.api.deps import obter_db
from app.schemas.schemas import LoginInput
from app.services.auth_service import AuthService
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/auth", tags=["Autenticação Centralizada"])

@router.post("/login")
def efetuar_login(dados: LoginInput, request: Request, db: Session = Depends(obter_db)):
    user = AuthService.autenticar_utilizador(db, dados.username, dados.password)
    ip = request.client.host if request.client else "127.0.0.1"
    
    if not user:
        AuditoriaService.registar_evento(db, dados.username, "FALHA_AUTENTICACAO", "Tentativa com credenciais inválidas", ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador ou palavra-passe incorreta.")
        
    token = AuthService.criar_token_jwt(user.username, user.role)
    AuditoriaService.registar_evento(db, user.username, "SUCESSO_AUTENTICACAO", "Token JWT gerado", ip)
    
    return {"access_token": token, "token_type": "bearer"}