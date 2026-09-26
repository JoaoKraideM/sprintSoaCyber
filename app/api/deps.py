from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
    """Controle de acesso baseado em perfis com esquema Bearer documentado no OpenAPI."""

    bearer = HTTPBearer(auto_error=False)

    def validador(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        db: Session = Depends(obter_db),
    ):
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais Bearer ausentes ou invalidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        try:
            payload = AuthService.validar_token_jwt(token)
            user = AuthService.obter_utilizador_por_email(db, payload["sub"])
            if not user or not user.status:
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
                "user_id": user.id,
                "nome": user.nome,
                "email": user.email,
                "role": role,
                "exp": payload["exp"],
            }

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    return validador
