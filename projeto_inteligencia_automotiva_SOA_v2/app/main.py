from fastapi import FastAPI
from app.core.middleware import seguranca_middleware_global
from app.api.auth import router as auth_router
from app.api.veiculos import router as veiculos_router
from app.db.session import Base, engine, SessionLocal
from app.models.modelos import UtilizadorModel, VeiculoModel
from app.core.security import gerar_hash_palavra_passe
import json

app = FastAPI(
    title="Plataforma de Inteligência Competitiva Automotiva (SOA & Cyber Secure)",
    description="Desafio 01 - Divisão Limpa em Camadas de Apresentação, Serviço e Dados.",
    version="2.0.0"
)

# Acoplamento dos Middlewares reutilizáveis de segurança da informação
app.middleware("http")(seguranca_middleware_global)

# Montagem modular dos Serviços independentes (SOA)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(veiculos_router, prefix="/api/v1")

@app.on_event("startup")
def inicializar_e_validar_dados():
    # Garante a migração das tabelas na camada de dados
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # Criação dos perfis base para validação do RBAC
    if not db.query(UtilizadorModel).filter_by(username="admin_bradesco").first():
        db.add(UtilizadorModel(username="admin_bradesco", password_hash=gerar_hash_palavra_passe("SenhaForte123"), role="admin"))
        db.add(UtilizadorModel(username="analista_mercado", password_hash=gerar_hash_palavra_passe("Analise789"), role="analista"))
    
    # Validação mandatória do Desafio: Inserção prévia da Ford Ranger Raptor
    if not db.query(VeiculoModel).filter_by(modelo="Ranger Raptor").first():
        pacote_raptor = {
            "Painel Digital": "12.4 polegadas",
            "Som": "Premium Bang & Olufsen",
            "Modos de Condução": "7 modos (incluindo Baja)",
            "Amortecedores": "FOX Live Valve 2.5"
        }
        raptor = VeiculoModel(
            marca="Ford", modelo="Ranger Raptor", versao="3.0 V6 Bi-Turbo",
            motorizacao="3.0L V6 EcoBoost Gasolina", potencia="397 cv",
            transmissao="Automática de 10 marchas", tracao="4x4 integral",
            preco_sugerido="Sob Consulta", pacote_equipamentos=json.dumps(pacote_raptor)
        )
        db.add(raptor)
    db.commit()
    db.close()