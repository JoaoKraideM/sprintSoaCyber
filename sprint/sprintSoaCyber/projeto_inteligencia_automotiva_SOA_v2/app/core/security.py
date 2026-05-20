import hashlib
import re

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def sanitizar_string(v: str) -> str:
    """Camada de apresentacao/validacao: previne XSS e command injection."""
    if not isinstance(v, str):
        return v
    v_clean = re.sub(r"<[^>]*>", "", v)
    v_clean = re.sub(r"[\\;`|]", "", v_clean)
    return v_clean.strip()


def normalizar_email(email: str) -> str:
    email_limpo = sanitizar_string(email).lower()
    if not EMAIL_REGEX.fullmatch(email_limpo):
        raise ValueError("Email invalido.")
    return email_limpo


def validar_forca_senha(password: str) -> None:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("A senha deve ter no minimo 8 caracteres.")


def _material_credencial(email: str, password: str) -> str:
    email_normalizado = normalizar_email(email)
    validar_forca_senha(password)
    return f"{email_normalizado}:{password}"


def gerar_hash_credencial(email: str, password: str) -> str:
    material = _material_credencial(email, password)
    return pwd_context.hash(material)


def verificar_hash_credencial(email: str, password: str, hash_armazenado: str) -> bool:
    material = _material_credencial(email, password)
    return pwd_context.verify(material, hash_armazenado)


def gerar_fingerprint_hash(hash_armazenado: str) -> str:
    return hashlib.sha256(hash_armazenado.encode("utf-8")).hexdigest()


def verificar_palavra_passe(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def gerar_hash_palavra_passe(password: str) -> str:
    return pwd_context.hash(password)
