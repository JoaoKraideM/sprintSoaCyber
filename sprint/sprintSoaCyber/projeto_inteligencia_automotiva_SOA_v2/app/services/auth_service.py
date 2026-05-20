import base64
import binascii
import json
from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    gerar_fingerprint_hash,
    gerar_hash_credencial,
    normalizar_email,
    verificar_hash_credencial,
    verificar_palavra_passe,
)
from app.models.modelos import UtilizadorModel


class AuthService:
    @staticmethod
    def cadastrar_utilizador(db: Session, email: str, password: str, role: str = "usuario") -> UtilizadorModel:
        email_normalizado = normalizar_email(email)

        existente = (
            db.query(UtilizadorModel)
            .filter(or_(UtilizadorModel.email == email_normalizado, UtilizadorModel.username == email_normalizado))
            .first()
        )
        if existente:
            raise ValueError("Utilizador ja cadastrado.")

        novo = UtilizadorModel(
            username=email_normalizado,
            email=email_normalizado,
            password_hash=gerar_hash_credencial(email_normalizado, password),
            role=role,
            ativo=True,
        )
        db.add(novo)
        db.commit()
        db.refresh(novo)
        return novo

    @staticmethod
    def obter_utilizador_por_email(db: Session, email: str):
        email_normalizado = normalizar_email(email)
        return (
            db.query(UtilizadorModel)
            .filter(or_(UtilizadorModel.email == email_normalizado, UtilizadorModel.username == email_normalizado))
            .first()
        )

    @staticmethod
    def autenticar_utilizador(db: Session, email: str, palavra_passe: str):
        user = AuthService.obter_utilizador_por_email(db, email)
        if not user or not user.ativo:
            return None

        try:
            if verificar_hash_credencial(user.email, palavra_passe, user.password_hash):
                return user
        except ValueError:
            return None

        # Compatibilidade com hash legado (senha sem email concatenado).
        if len(palavra_passe) >= 8 and verificar_palavra_passe(palavra_passe, user.password_hash):
            user.password_hash = gerar_hash_credencial(user.email, palavra_passe)
            db.commit()
            db.refresh(user)
            return user

        return None

    @staticmethod
    def _dados_para_base64(username: str, role: str, cred_fingerprint: str) -> str:
        dados = {"sub": username, "role": role, "cred_fingerprint": cred_fingerprint}
        dados_json = json.dumps(dados, separators=(",", ":"), ensure_ascii=False)
        return base64.b64encode(dados_json.encode("utf-8")).decode("utf-8")

    @staticmethod
    def _base64_para_dados(dados_base64: str) -> dict:
        dados_json = base64.b64decode(dados_base64, validate=True).decode("utf-8")
        dados = json.loads(dados_json)
        if not isinstance(dados, dict):
            raise ValueError("Dados base64 invalidos.")
        return dados

    @staticmethod
    def criar_token_jwt(username: str, role: str, cred_fingerprint: str) -> str:
        agora_utc = datetime.now(timezone.utc)
        expira_em = agora_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        dados_encriptar = {
            "sub": username,
            "role": role,
            "cred_fingerprint": cred_fingerprint,
            "dados_base64": AuthService._dados_para_base64(username, role, cred_fingerprint),
            "iat": int(agora_utc.timestamp()),
            "exp": int(expira_em.timestamp()),
        }
        return jwt.encode(dados_encriptar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def validar_token_jwt(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"require": ["sub", "role", "iat", "exp", "dados_base64", "cred_fingerprint"]},
            )
        except ExpiredSignatureError as exc:
            raise ValueError("Token expirado.") from exc
        except InvalidTokenError as exc:
            raise ValueError("Token invalido.") from exc

        try:
            dados = AuthService._base64_para_dados(payload["dados_base64"])
        except (KeyError, ValueError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error) as exc:
            raise ValueError("Dados em base64 invalidos no token.") from exc

        if (
            dados.get("sub") != payload.get("sub")
            or dados.get("role") != payload.get("role")
            or dados.get("cred_fingerprint") != payload.get("cred_fingerprint")
        ):
            raise ValueError("Inconsistencia entre payload JWT e dados em base64.")

        return {
            "sub": payload["sub"],
            "role": payload["role"],
            "cred_fingerprint": payload["cred_fingerprint"],
            "iat": payload["iat"],
            "exp": payload["exp"],
            "dados": dados,
        }

    @staticmethod
    def fingerprint_atual_do_utilizador(user: UtilizadorModel) -> str:
        return gerar_fingerprint_hash(user.password_hash)
