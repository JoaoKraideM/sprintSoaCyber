from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db, verificar_rbac
from app.schemas.schemas import CadastroVeiculoInput, ConsultaVeiculoInput
from app.services.event_bus import EventBus, EventoDominio
from app.services.veiculo_service import VeiculoService

router = APIRouter(prefix="/veiculos", tags=["Catalogo e Inteligencia Automotiva"])


@router.post("/comparar", status_code=status.HTTP_200_OK)
def comparar_veiculos(
    payload: ConsultaVeiculoInput,
    request: Request,
    token_data: dict = Depends(verificar_rbac(["admin", "analista", "user"])),
    db: Session = Depends(obter_db),
):
    ip = request.client.host if request.client else "127.0.0.1"

    resposta = VeiculoService.processar_analise_competitiva(db, payload)

    if token_data["role"] == "analista":
        EventBus.publicar(
            db,
            EventoDominio(
                nome="EXTRACAO_COMPETITIVA",
                user_id=token_data["user_id"],
                ip_origem=ip,
                user_agent=request.headers.get("user-agent"),
                dados_depois={"marca": payload.marca, "modelo": payload.modelo, "versao": payload.versao},
            ),
        )

    return resposta


@router.post("", status_code=status.HTTP_201_CREATED)
def cadastrar_veiculo(
    payload: CadastroVeiculoInput,
    request: Request,
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    ip = request.client.host if request.client else "127.0.0.1"

    existente = VeiculoService.procurar_veiculo_especifico(db, payload.marca, payload.modelo, payload.versao)
    if existente:
        raise HTTPException(status_code=400, detail="Veiculo ja cadastrado no catalogo.")

    veiculo_salvo, metrica = VeiculoService.registar_novo_veiculo(db, payload, token_data["user_id"])

    EventBus.publicar(
        db,
        EventoDominio(
            nome="CADASTRO_VEICULO",
            user_id=token_data["user_id"],
            metrica_veiculo_id=metrica.id if metrica else None,
            ip_origem=ip,
            user_agent=request.headers.get("user-agent"),
            dados_depois={
                "veiculo_id": veiculo_salvo.id,
                "marca": payload.marca,
                "modelo": payload.modelo,
                "versao": payload.versao,
            },
        ),
    )

    return {"status": "sucesso", "id": veiculo_salvo.id, "metrica_id": metrica.id if metrica else None}
