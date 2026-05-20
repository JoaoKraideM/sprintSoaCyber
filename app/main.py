from decimal import Decimal
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
from app.models.modelos import MetricaVeiculoModel, ModeloModel, UserModel, VeiculoModel, VersaoModel

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


@app.on_event("startup")
def inicializar_e_validar_dados():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = db.query(UserModel).filter_by(email="admin_bradesco@sistema.local").first()
        if not admin:
            admin = UserModel(
                nome="Admin Bradesco",
                email="admin_bradesco@sistema.local",
                password=gerar_hash_credencial("admin_bradesco@sistema.local", "SenhaForte123"),
                role="admin",
                status=True,
            )
            db.add(admin)
            db.flush()

        analista = db.query(UserModel).filter_by(email="analista_mercado@sistema.local").first()
        if not analista:
            analista = UserModel(
                nome="Analista Mercado",
                email="analista_mercado@sistema.local",
                password=gerar_hash_credencial("analista_mercado@sistema.local", "Analise789"),
                role="analista",
                status=True,
            )
            db.add(analista)
            db.flush()

        modelo = db.query(ModeloModel).filter_by(marca="Ford", nome="Ranger Raptor").first()
        if not modelo:
            modelo = ModeloModel(marca="Ford", nome="Ranger Raptor")
            db.add(modelo)
            db.flush()

        versao = db.query(VersaoModel).filter_by(modelo_id=modelo.id, nome="3.0 V6 Bi-Turbo").first()
        if not versao:
            versao = VersaoModel(modelo_id=modelo.id, nome="3.0 V6 Bi-Turbo")
            db.add(versao)
            db.flush()

        veiculo = (
            db.query(VeiculoModel)
            .filter(
                VeiculoModel.versao_id == versao.id,
                VeiculoModel.motorizacao == "3.0L V6 EcoBoost Gasolina",
                VeiculoModel.potencia_cv == 397,
            )
            .first()
        )
        if not veiculo:
            veiculo = VeiculoModel(
                versao_id=versao.id,
                motorizacao="3.0L V6 EcoBoost Gasolina",
                potencia_cv=397,
                transmissao="Automatica de 10 marchas",
                tracao="4x4 integral",
                status=True,
            )
            db.add(veiculo)
            db.flush()

        metrica = (
            db.query(MetricaVeiculoModel)
            .filter(MetricaVeiculoModel.veiculo_id == veiculo.id, MetricaVeiculoModel.user_id == admin.id)
            .first()
        )
        if not metrica:
            metrica = MetricaVeiculoModel(
                veiculo_id=veiculo.id,
                user_id=admin.id,
                preco_sugerido=Decimal("0.00"),
                pacote_equipamentos={
                    "Painel Digital": "12.4 polegadas",
                    "Som": "Premium Bang & Olufsen",
                    "Modos de Conducao": "7 modos (incluindo Baja)",
                    "Amortecedores": "FOX Live Valve 2.5",
                },
                observacao="Seed inicial Ford Ranger Raptor",
            )
            db.add(metrica)

        db.commit()
    finally:
        db.close()
