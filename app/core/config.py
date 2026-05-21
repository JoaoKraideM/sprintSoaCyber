import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _ler_int(nome: str, padrao: int) -> int:
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    try:
        return int(valor)
    except ValueError:
        return padrao


def _ler_lista(nome: str, padrao: list[str]) -> list[str]:
    valor = os.getenv(nome)
    if not valor:
        return padrao
    return [item.strip() for item in valor.split(",") if item.strip()]


class Settings:
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = _ler_int("SERVER_PORT", 8000)

    SECRET_KEY: str = os.getenv("SECRET_KEY", "ChavePadraoDeSegurancaParaDesenvolvimento2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _ler_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    PAYLOAD_SECRET_HMAC: bytes = os.getenv("PAYLOAD_SECRET_HMAC", "IntegrityKeyDefault").encode()
    MAX_CONTENT_LENGTH: int = _ler_int("MAX_CONTENT_LENGTH_KB", 50) * 1024

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./veiculos_db.db")

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(Path("data") / "uploads"))
    MAX_UPLOAD_FILE_SIZE: int = _ler_int("MAX_UPLOAD_FILE_SIZE_MB", 10) * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = _ler_lista("ALLOWED_UPLOAD_EXTENSIONS", [".xlsx", ".xls"])
    ALLOWED_UPLOAD_CONTENT_TYPES: list[str] = _ler_lista(
        "ALLOWED_UPLOAD_CONTENT_TYPES",
        [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream",
        ],
    )


settings = Settings()
