from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import settings


SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")


def _url_sem_banco() -> str:
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "mysql":
        raise RuntimeError("O script schema.sql e MySQL. Configure DATABASE_URL ou DB_DRIVER com mysql+pymysql.")
    return url.set(database="").render_as_string(hide_password=False)


def _ler_comandos_sql(caminho: Path) -> list[str]:
    conteudo = caminho.read_text(encoding="utf-8")
    comandos = []

    for bloco in conteudo.split(";"):
        comando = "\n".join(
            linha for linha in bloco.splitlines()
            if linha.strip() and not linha.strip().startswith("--")
        ).strip()
        if comando:
            comandos.append(comando)

    return comandos


def inicializar_banco(caminho_schema: Path = SCHEMA_PATH) -> int:
    engine = create_engine(_url_sem_banco(), pool_pre_ping=True)
    comandos = _ler_comandos_sql(caminho_schema)

    with engine.begin() as conexao:
        for comando in comandos:
            conexao.execute(text(comando))

    return len(comandos)


if __name__ == "__main__":
    total = inicializar_banco()
    print(f"Banco inicializado com sucesso. Comandos executados: {total}")
