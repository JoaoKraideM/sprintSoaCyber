import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router
from app.api.veiculos import router as veiculos_router
from app.core.middleware import seguranca_middleware_global
from app.core.security import gerar_hash_credencial
from app.db.session import Base, SessionLocal, engine
from app.models.modelos import UtilizadorModel, VeiculoModel

app = FastAPI(
    title="Plataforma de Inteligencia Competitiva Automotiva (SOA + Cyber Secure)",
    description="Base de cadastro, autenticacao JWT e upload Excel com arquitetura em camadas.",
    version="3.0.0",
)

# Acoplamento dos middlewares reutilizaveis de seguranca.
app.middleware("http")(seguranca_middleware_global)

# Montagem modular dos servicos independentes (SOA).
app.include_router(auth_router, prefix="/api/v1")
app.include_router(veiculos_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")

_web_dir = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(_web_dir)), name="static")


@app.get("/", include_in_schema=False)
def servir_site():
    return FileResponse(_web_dir / "index.html")


@app.on_event("startup")
def inicializar_e_validar_dados():
    # Garante a migracao das tabelas na camada de dados.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Criacao dos perfis base para validacao do RBAC.
        if not db.query(UtilizadorModel).filter_by(email="admin_bradesco@sistema.local").first():
            db.add(
                UtilizadorModel(
                    username="admin_bradesco@sistema.local",
                    email="admin_bradesco@sistema.local",
                    password_hash=gerar_hash_credencial("admin_bradesco@sistema.local", "SenhaForte123"),
                    role="admin",
                )
            )

        if not db.query(UtilizadorModel).filter_by(email="analista_mercado@sistema.local").first():
            db.add(
                UtilizadorModel(
                    username="analista_mercado@sistema.local",
                    email="analista_mercado@sistema.local",
                    password_hash=gerar_hash_credencial("analista_mercado@sistema.local", "Analise789"),
                    role="analista",
                )
            )

        # Validacao mandataria do desafio: insercao previa da Ford Ranger Raptor.
        if not db.query(VeiculoModel).filter_by(modelo="Ranger Raptor").first():
            pacote_raptor = {
                "Painel Digital": "12.4 polegadas",
                "Som": "Premium Bang & Olufsen",
                "Modos de Conducao": "7 modos (incluindo Baja)",
                "Amortecedores": "FOX Live Valve 2.5",
            }
            raptor = VeiculoModel(
                marca="Ford",
                modelo="Ranger Raptor",
                versao="3.0 V6 Bi-Turbo",
                motorizacao="3.0L V6 EcoBoost Gasolina",
                potencia="397 cv",
                transmissao="Automatica de 10 marchas",
                tracao="4x4 integral",
                preco_sugerido="Sob Consulta",
                pacote_equipamentos=json.dumps(pacote_raptor),
            )
            db.add(raptor)

        db.commit()
    finally:
        db.close()
