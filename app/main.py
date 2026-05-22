from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router
from app.api.veiculos import router as veiculos_router
from app.core.middleware import seguranca_middleware_global
from app.db.session import engine

app = FastAPI(
    title="Plataforma de Inteligencia Competitiva Automotiva (SOA + Cyber Secure)",
    description="Base de cadastro, autenticacao JWT e upload Excel com arquitetura em camadas.",
    version="3.1.0",
)

app.middleware("http")(seguranca_middleware_global)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(veiculos_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")

_web_dir = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(_web_dir)), name="static")


@app.get("/", include_in_schema=False)
def servir_site():
    return FileResponse(_web_dir / "index.html")


@app.get("/health/db", tags=["Health"])
def verificar_conexao_banco():
    with engine.connect() as conexao:
        conexao.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectado"}
