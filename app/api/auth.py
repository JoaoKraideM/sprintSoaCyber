from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db
from app.core.config import settings
from app.schemas.schemas import CadastroUsuarioInput, LoginInput
from app.services.auth_service import AuthService
from app.services.event_bus import EventBus, EventoDominio

router = APIRouter(prefix="/auth", tags=["Autenticacao Centralizada"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def cadastrar_utilizador(dados: CadastroUsuarioInput, request: Request, db: Session = Depends(obter_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    # Cadastro publico cria apenas perfil user para evitar elevacao de privilegio.
    role_segura = "user"

    try:
        user = AuthService.cadastrar_utilizador(
            db,
            dados.email,
            dados.password,
            role_segura,
            nome=dados.nome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    EventBus.publicar(
        db,
        EventoDominio(
            nome="SUCESSO_CADASTRO",
            user_id=user.id,
            ip_origem=ip,
            user_agent=user_agent,
            dados_depois={"email": user.email, "role": user.role},
        ),
    )

    return {
        "status": "sucesso",
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "role": user.role,
    }


@router.post("/login")
def efetuar_login(dados: LoginInput, request: Request, db: Session = Depends(obter_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")
    email_login = dados.email

    user = AuthService.autenticar_utilizador(db, email_login, dados.password)
    if not user:
        user_existente = AuthService.obter_utilizador_por_email(db, email_login)
        AuthService.registar_log_auth(
            db,
            user_id=user_existente.id if user_existente else None,
            address=email_login,
            ip=ip,
            user_agent=user_agent,
            status=False,
        )
        if user_existente:
            EventBus.publicar(
                db,
                EventoDominio(
                    nome="FALHA_AUTENTICACAO",
                    user_id=user_existente.id,
                    ip_origem=ip,
                    user_agent=user_agent,
                    dados_depois={"email": email_login},
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador ou palavra-passe incorreta.",
        )

    fingerprint = AuthService.fingerprint_atual_do_utilizador(user)
    token = AuthService.criar_token_jwt(user.email, user.role, fingerprint)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    AuthService.registar_log_auth(
        db,
        user_id=user.id,
        address=user.email,
        ip=ip,
        user_agent=user_agent,
        status=True,
        expires_at=expires_at,
    )

    EventBus.publicar(
        db,
        EventoDominio(
            nome="SUCESSO_AUTENTICACAO",
            user_id=user.id,
            ip_origem=ip,
            user_agent=user_agent,
            dados_depois={"email": user.email, "role": user.role},
        ),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "email": user.email,
        "role": user.role,
        "nome": user.nome,
    }
