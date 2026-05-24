import hashlib
import hmac
import base64
import re
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import settings

EMAIL_VALUE_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SENSITIVE_KEYS = {
    "password",
    "senha",
    "token",
    "access_token",
    "authorization",
    "secret",
    "db_password",
}
PII_KEYS = {"email", "address", "ip", "user_agent"}


def pseudonimizar(valor: str) -> str:
    digest = hmac.new(settings.PAYLOAD_SECRET_HMAC, valor.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"pseudo:{digest[:24]}"


def mascarar_texto(texto: str) -> str:
    return EMAIL_VALUE_REGEX.sub(lambda match: pseudonimizar(match.group(0).lower()), texto)


def sanitizar_para_auditoria(valor: Any, chave: str | None = None) -> Any:
    if not settings.ANONYMIZE_AUDIT_PII:
        return valor

    chave_normalizada = (chave or "").lower()
    if chave_normalizada in SENSITIVE_KEYS:
        return "[REMOVIDO]"

    if isinstance(valor, dict):
        return {k: sanitizar_para_auditoria(v, str(k)) for k, v in valor.items()}

    if isinstance(valor, list):
        return [sanitizar_para_auditoria(item, chave) for item in valor]

    if isinstance(valor, str):
        if chave_normalizada in PII_KEYS:
            return pseudonimizar(valor)
        return mascarar_texto(valor)

    return valor


def _fernet() -> Fernet:
    segredo = settings.DATA_ENCRYPTION_KEY.encode("utf-8") if settings.DATA_ENCRYPTION_KEY else settings.PAYLOAD_SECRET_HMAC
    if settings.DATA_ENCRYPTION_KEY:
        try:
            return Fernet(segredo)
        except ValueError:
            pass

    chave = base64.urlsafe_b64encode(hashlib.sha256(segredo).digest())
    return Fernet(chave)


def criptografar_bytes(conteudo: bytes) -> bytes:
    return _fernet().encrypt(conteudo)


def descriptografar_bytes(conteudo: bytes) -> bytes:
    return _fernet().decrypt(conteudo)
