from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db, verificar_rbac
from app.schemas.schemas import AtualizacaoVeiculoInput, CadastroVeiculoInput, ConsultaVeiculoInput
from app.services.event_bus import EventBus, EventoDominio
from app.services.veiculo_service import VeiculoService

router = APIRouter(prefix="/veiculos", tags=["Catalogo e Inteligencia Automotiva"])



@router.get("", status_code=status.HTTP_200_OK)
def listar_veiculos(
    marca: str | None = None,
    modelo: str | None = None,
    versao: str | None = None,
    skip: int = 0,
    limit: int = 50,
    token_data: dict = Depends(verificar_rbac(["admin", "analista", "user"])),
    db: Session = Depends(obter_db),
):
    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Parametros de paginacao invalidos.")

    registros = VeiculoService.listar_veiculos(db, marca, modelo, versao, skip, limit)
    itens = []
    for veiculo, marca_db, modelo_db, versao_db in registros:
        metrica = VeiculoService.obter_ultima_metrica(db, veiculo.id)
        itens.append({
            "id": veiculo.id,
            "marca": marca_db,
            "modelo": modelo_db,
            "versao": versao_db,
            "motorizacao": veiculo.motorizacao,
            "potencia_cv": veiculo.potencia_cv,
            "transmissao": veiculo.transmissao,
            "tracao": veiculo.tracao,
            "preco_sugerido": str(metrica.preco_sugerido) if metrica and metrica.preco_sugerido is not None else None,
            "pacote_equipamentos": metrica.pacote_equipamentos if metrica else {},
            "observacao": metrica.observacao if metrica else None,
            "ativo": veiculo.status,
        })
    return {"itens": itens, "skip": skip, "limit": limit, "total": len(itens)}


@router.get("/comparar", status_code=status.HTTP_200_OK)
def comparar_veiculos_get(
    marca: str,
    modelo: str,
    versao: str,
    atributos_desejados: list[str] = Query(default=[]),
    token_data: dict = Depends(verificar_rbac(["admin", "analista", "user"])),
    db: Session = Depends(obter_db),
):
    payload = ConsultaVeiculoInput(
        marca=marca,
        modelo=modelo,
        versao=versao,
        atributos_desejados=atributos_desejados,
    )
    return VeiculoService.processar_analise_competitiva(db, payload)


@router.get("/{veiculo_id}", status_code=status.HTTP_200_OK)
def obter_veiculo(
    veiculo_id: int,
    token_data: dict = Depends(verificar_rbac(["admin", "analista", "user"])),
    db: Session = Depends(obter_db),
):
    registro = VeiculoService.obter_veiculo_por_id(db, veiculo_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Veiculo nao encontrado.")

    veiculo, marca, modelo, versao = registro
    metrica = VeiculoService.obter_ultima_metrica(db, veiculo.id)
    return {
        "id": veiculo.id,
        "marca": marca,
        "modelo": modelo,
        "versao": versao,
        "motorizacao": veiculo.motorizacao,
        "potencia_cv": veiculo.potencia_cv,
        "transmissao": veiculo.transmissao,
        "tracao": veiculo.tracao,
        "preco_sugerido": str(metrica.preco_sugerido) if metrica and metrica.preco_sugerido is not None else None,
        "pacote_equipamentos": metrica.pacote_equipamentos if metrica else {},
        "observacao": metrica.observacao if metrica else None,
        "ativo": veiculo.status,
    }


@router.patch("/{veiculo_id}", status_code=status.HTTP_200_OK)
def atualizar_veiculo(
    veiculo_id: int,
    payload: AtualizacaoVeiculoInput,
    request: Request,
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    try:
        registro = VeiculoService.atualizar_veiculo(db, veiculo_id, payload, token_data["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if not registro:
        raise HTTPException(status_code=404, detail="Veiculo nao encontrado.")

    veiculo, marca, modelo, versao = registro
    EventBus.publicar(
        db,
        EventoDominio(
            nome="ATUALIZACAO_VEICULO",
            user_id=token_data["user_id"],
            ip_origem=request.client.host if request.client else "127.0.0.1",
            user_agent=request.headers.get("user-agent"),
            dados_depois={"veiculo_id": veiculo.id, "marca": marca, "modelo": modelo, "versao": versao},
        ),
    )
    return {"status": "sucesso", "id": veiculo.id, "marca": marca, "modelo": modelo, "versao": versao}


@router.delete("/{veiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_veiculo(
    veiculo_id: int,
    request: Request,
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    if not VeiculoService.remover_veiculo(db, veiculo_id):
        raise HTTPException(status_code=404, detail="Veiculo nao encontrado.")

    EventBus.publicar(
        db,
        EventoDominio(
            nome="EXCLUSAO_VEICULO",
            user_id=token_data["user_id"],
            ip_origem=request.client.host if request.client else "127.0.0.1",
            user_agent=request.headers.get("user-agent"),
            dados_depois={"veiculo_id": veiculo_id},
        ),
    )
    return None


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
