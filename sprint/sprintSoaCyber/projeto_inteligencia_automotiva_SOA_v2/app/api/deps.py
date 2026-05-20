from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.auth_service import AuthService


def obter_db():
    """Injecao de dependencia modular da sessao SQL."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verificar_rbac(papeis_permitidos: list):
    """Controle de acesso baseado em perfis com validacao criptografica do JWT."""

    def validador(authorization: str = Header(...), db: Session = Depends(obter_db)):
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esquema de autenticacao invalido.",
            )

        token = authorization.split(" ", 1)[1]
        try:
            payload = AuthService.validar_token_jwt(token)
            user = AuthService.obter_utilizador_por_email(db, payload["sub"])
            if not user or not user.ativo:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Utilizador inexistente ou inativo.",
                )

            fingerprint_atual = AuthService.fingerprint_atual_do_utilizador(user)
            if payload["cred_fingerprint"] != fingerprint_atual:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token nao corresponde ao estado atual da credencial.",
                )

            role = payload.get("role")
            if role not in papeis_permitidos:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado para a sua funcao.",
                )

            return {
                "username": user.username,
                "email": user.email,
                "role": role,
                "exp": payload["exp"],
            }

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

    return validador
