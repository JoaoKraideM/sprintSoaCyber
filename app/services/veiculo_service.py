from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.modelos import MarcaModel, MetricaVeiculoModel, ModeloModel, VeiculoModel, VersaoModel
from app.schemas.schemas import CadastroVeiculoInput, ConsultaVeiculoInput


class VeiculoService:
    """Camada de servico core: isola regras de negocio do catalogo automotivo."""

    @staticmethod
    def procurar_veiculo_especifico(db: Session, marca: str, modelo: str, versao: str):
        return (
            db.query(VeiculoModel)
            .join(VersaoModel, VeiculoModel.versao_id == VersaoModel.id)
            .join(ModeloModel, VersaoModel.modelo_id == ModeloModel.id)
            .join(MarcaModel, ModeloModel.marca_id == MarcaModel.id)
            .filter(
                MarcaModel.nome == marca,
                ModeloModel.nome == modelo,
                VersaoModel.nome == versao,
                VeiculoModel.status.is_(True),
            )
            .first()
        )

    @staticmethod
    def obter_ultima_metrica(db: Session, veiculo_id: int):
        return (
            db.query(MetricaVeiculoModel)
            .filter(MetricaVeiculoModel.veiculo_id == veiculo_id)
            .order_by(
                MetricaVeiculoModel.create_date.desc(),
                MetricaVeiculoModel.hour_date.desc(),
                MetricaVeiculoModel.id.desc(),
            )
            .first()
        )

    @staticmethod
    def processar_analise_competitiva(db: Session, payload: ConsultaVeiculoInput) -> dict:
        veiculo = VeiculoService.procurar_veiculo_especifico(db, payload.marca, payload.modelo, payload.versao)
        metrica = VeiculoService.obter_ultima_metrica(db, veiculo.id) if veiculo else None

        equipamentos_map = metrica.pacote_equipamentos if metrica and metrica.pacote_equipamentos else {}

        saida_padronizada = {
            "marca": payload.marca,
            "modelo": payload.modelo,
            "versao": payload.versao,
            "dados_tecnicos_principais": {
                "motorizacao": veiculo.motorizacao if veiculo else "vazio / nao disponivel",
                "potencia_cv": veiculo.potencia_cv if veiculo else "vazio / nao disponivel",
                "transmissao": veiculo.transmissao if veiculo else "vazio / nao disponivel",
                "tracao": veiculo.tracao if veiculo else "vazio / nao disponivel",
                "preco_sugerido": str(metrica.preco_sugerido) if metrica else "vazio / nao disponivel",
            },
            "equipamentos_pesquisados_livres": {},
        }

        for atributo in payload.atributos_desejados:
            saida_padronizada["equipamentos_pesquisados_livres"][atributo] = equipamentos_map.get(
                atributo,
                "vazio / nao disponivel",
            )

        return saida_padronizada

    @staticmethod
    def _obter_ou_criar_modelo_versao(db: Session, marca: str, modelo: str, versao: str):
        marca_db = db.query(MarcaModel).filter(MarcaModel.nome == marca).first()
        if not marca_db:
            marca_db = MarcaModel(nome=marca)
            db.add(marca_db)
            db.flush()

        modelo_db = db.query(ModeloModel).filter(ModeloModel.marca_id == marca_db.id, ModeloModel.nome == modelo).first()
        if not modelo_db:
            modelo_db = ModeloModel(marca_id=marca_db.id, nome=modelo)
            db.add(modelo_db)
            db.flush()

        versao_db = db.query(VersaoModel).filter(VersaoModel.modelo_id == modelo_db.id, VersaoModel.nome == versao).first()
        if not versao_db:
            versao_db = VersaoModel(modelo_id=modelo_db.id, nome=versao)
            db.add(versao_db)
            db.flush()

        return marca_db, modelo_db, versao_db

    @staticmethod
    def registar_novo_veiculo(db: Session, v: CadastroVeiculoInput, user_id: int):
        _, _, versao_db = VeiculoService._obter_ou_criar_modelo_versao(db, v.marca, v.modelo, v.versao)

        existente = (
            db.query(VeiculoModel)
            .filter(
                VeiculoModel.versao_id == versao_db.id,
                VeiculoModel.motorizacao == v.motorizacao,
                VeiculoModel.potencia_cv == v.potencia_cv,
                VeiculoModel.transmissao == v.transmissao,
                VeiculoModel.tracao == v.tracao,
                VeiculoModel.status.is_(True),
            )
            .first()
        )
        if existente:
            return existente, VeiculoService.obter_ultima_metrica(db, existente.id)

        novo = VeiculoModel(
            versao_id=versao_db.id,
            motorizacao=v.motorizacao,
            potencia_cv=v.potencia_cv,
            transmissao=v.transmissao,
            tracao=v.tracao,
            status=True,
        )
        db.add(novo)
        db.flush()

        metrica = MetricaVeiculoModel(
            veiculo_id=novo.id,
            user_id=user_id,
            preco_sugerido=Decimal(v.preco_sugerido),
            pacote_equipamentos=v.pacote_equipamentos,
            observacao=v.observacao,
        )
        db.add(metrica)
        db.commit()
        db.refresh(novo)
        db.refresh(metrica)

        return novo, metrica

    @staticmethod
    def importar_registros_excel(
        db: Session,
        user_id: int,
        marca: str,
        modelo: str,
        registros: list[dict[str, Any]],
        observacao: str,
    ) -> dict:
        metricas_criadas = 0
        veiculos_criados = 0
        primeira_metrica_id = None
        versoes_importadas = []
        itens_importados = []

        try:
            for registro in registros:
                _, _, versao_db = VeiculoService._obter_ou_criar_modelo_versao(
                    db=db,
                    marca=marca,
                    modelo=modelo,
                    versao=registro["versao"],
                )

                veiculo = (
                    db.query(VeiculoModel)
                    .filter(
                        VeiculoModel.versao_id == versao_db.id,
                        VeiculoModel.motorizacao == registro["motorizacao"],
                        VeiculoModel.potencia_cv == registro["potencia_cv"],
                        VeiculoModel.transmissao == registro["transmissao"],
                        VeiculoModel.tracao == registro["tracao"],
                        VeiculoModel.status.is_(True),
                    )
                    .first()
                )

                if not veiculo:
                    veiculo = VeiculoModel(
                        versao_id=versao_db.id,
                        motorizacao=registro["motorizacao"],
                        potencia_cv=registro["potencia_cv"],
                        transmissao=registro["transmissao"],
                        tracao=registro["tracao"],
                        status=True,
                    )
                    db.add(veiculo)
                    db.flush()
                    veiculos_criados += 1

                metrica = MetricaVeiculoModel(
                    veiculo_id=veiculo.id,
                    user_id=user_id,
                    preco_sugerido=None,
                    pacote_equipamentos=registro["pacote_equipamentos"],
                    observacao=observacao,
                )
                db.add(metrica)
                db.flush()

                primeira_metrica_id = primeira_metrica_id or metrica.id
                versoes_importadas.append(registro["versao"])
                metricas_criadas += 1
                itens_importados.append(
                    {
                        "versao": registro["versao"],
                        "veiculo_id": veiculo.id,
                        "metrica_id": metrica.id,
                    }
                )

            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
            raise

        return {
            "primeira_metrica_id": primeira_metrica_id,
            "versoes_importadas": versoes_importadas,
            "itens_importados": itens_importados,
            "veiculos_criados": veiculos_criados,
            "metricas_criadas": metricas_criadas,
        }
