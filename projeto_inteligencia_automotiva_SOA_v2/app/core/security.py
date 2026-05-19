import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def sanitizar_string(v: str) -> str:
    """Camada de Apresentação/Validação: Previne XSS e Command Injection"""
    if not isinstance(v, str):
        return v
    v_clean = re.sub(r"<[^>]*>", "", v)
    v_clean = re.sub(r"[\\;`|]", "", v_clean)
    return v_clean.strip()

def verificar_palavra_passe(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def gerar_hash_palavra_passe(password: str) -> str:
    return pwd_context.hash(password)