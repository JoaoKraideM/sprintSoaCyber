import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

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


def _montar_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    db_driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    if db_driver.startswith("sqlite"):
        return os.getenv("SQLITE_DATABASE_URL", "sqlite:///./veiculos_db.db")

    return URL.create(
        drivername=db_driver,
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "") or None,
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=_ler_int("DB_PORT", 3306),
        database=os.getenv("DB_NAME", "veiculos_db"),
        query={"charset": os.getenv("DB_CHARSET", "utf8mb4")},
    ).render_as_string(hide_password=False)


class Settings:
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = _ler_int("SERVER_PORT", 8000)

    SECRET_KEY: str = os.getenv("SECRET_KEY", "ChavePadraoDeSegurancaParaDesenvolvimento2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _ler_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    PAYLOAD_SECRET_HMAC: bytes = os.getenv("PAYLOAD_SECRET_HMAC", "IntegrityKeyDefault").encode()
    MAX_CONTENT_LENGTH: int = _ler_int("MAX_CONTENT_LENGTH_KB", 50) * 1024

    DB_DRIVER: str = os.getenv("DB_DRIVER", "mysql+pymysql")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = _ler_int("DB_PORT", 3306)
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "veiculos_db")
    DB_CHARSET: str = os.getenv("DB_CHARSET", "utf8mb4")
    DATABASE_URL: str = _montar_database_url()

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
