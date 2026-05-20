from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import obter_db, verificar_rbac
from app.schemas.schemas import ConsultaVeiculoInput, CadastroVeiculoInput
from app.services.veiculo_service import VeiculoService
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/veiculos", tags=["Catálogo e Inteligência Automotiva"])

@router.post("/comparar", status_code=status.HTTP_200_OK)
def comparar_veiculos(payload: ConsultaVeiculoInput, request: Request, token_data: dict = Depends(verificar_rbac(["admin", "analista", "usuario"])), db: Session = Depends(obter_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    
    # Executa a inteligência de negócios isolada na camada de Serviço
    resposta = VeiculoService.processar_analise_competitiva(db, payload)
    
    # Auditoria de Cybersecurity ativa para relatórios massivos
    if token_data["role"] == "analista":
        AuditoriaService.registar_evento(db, token_data["email"], "EXTRACAO_COMPETITIVA", f"Pesquisa sobre {payload.marca} {payload.modelo}", ip)
        
    return resposta

@router.post("", status_code=status.HTTP_201_CREATED)
def cadastrar_veiculo(payload: CadastroVeiculoInput, request: Request, token_data: dict = Depends(verificar_rbac(["admin"])), db: Session = Depends(obter_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    existente = VeiculoService.procurar_veiculo_especifico(db, payload.marca, payload.modelo, payload.versao)
    
    if existente:
        raise HTTPException(status_code=400, detail="Veículo já cadastrado no catálogo.")
        
    veiculo_salvo = VeiculoService.registar_novo_veiculo(db, payload)
    AuditoriaService.registar_evento(db, token_data["email"], "CADASTRO_VEICULO", f"Inserido {payload.marca} {payload.modelo}", ip)
    return {"status": "sucesso", "id": veiculo_salvo.id}
