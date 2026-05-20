import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.modelos import LogModel, MetricaVeiculoModel, ModeloModel, VeiculoModel, VersaoModel

logger = logging.getLogger("AuditoriaService")


class AuditoriaService:
    @staticmethod
    def _obter_ou_criar_metrica_sistema(db: Session, user_id: int) -> int:
        metrica = (
            db.query(MetricaVeiculoModel)
            .filter(MetricaVeiculoModel.user_id == user_id, MetricaVeiculoModel.observacao == "metrica_sistema")
            .first()
        )
        if metrica:
            return metrica.id

        modelo = db.query(ModeloModel).filter(ModeloModel.marca == "Sistema", ModeloModel.nome == "Interno").first()
        if not modelo:
            modelo = ModeloModel(marca="Sistema", nome="Interno")
            db.add(modelo)
            db.flush()

        versao = db.query(VersaoModel).filter(VersaoModel.modelo_id == modelo.id, VersaoModel.nome == "1.0").first()
        if not versao:
            versao = VersaoModel(modelo_id=modelo.id, nome="1.0")
            db.add(versao)
            db.flush()

        veiculo = (
            db.query(VeiculoModel)
            .filter(
                VeiculoModel.versao_id == versao.id,
                VeiculoModel.motorizacao == "N/A",
                VeiculoModel.potencia_cv == 1,
            )
            .first()
        )
        if not veiculo:
            veiculo = VeiculoModel(
                versao_id=versao.id,
                motorizacao="N/A",
                potencia_cv=1,
                transmissao="N/A",
                tracao="N/A",
                status=True,
            )
            db.add(veiculo)
            db.flush()

        metrica = MetricaVeiculoModel(
            veiculo_id=veiculo.id,
            user_id=user_id,
            preco_sugerido=Decimal("0.00"),
            pacote_equipamentos={},
            observacao="metrica_sistema",
        )
        db.add(metrica)
        db.flush()
        return metrica.id

    @staticmethod
    def registar_evento(
        db: Session,
        user_id: int,
        acao: str,
        ip_origem: str | None = None,
        user_agent: str | None = None,
        metrica_veiculo_id: int | None = None,
        dados_antes: dict | None = None,
        dados_depois: dict | None = None,
    ):
        """Registra eventos na tabela logs seguindo o novo schema relacional."""
        metrica_id = metrica_veiculo_id or AuditoriaService._obter_ou_criar_metrica_sistema(db, user_id)

        log = LogModel(
            metrica_veiculo_id=metrica_id,
            user_id=user_id,
            acao=(acao or "ACAO")[0:50],
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            ip=ip_origem,
            user_agent=(user_agent or "")[0:50] or None,
        )
        db.add(log)
        db.commit()
        logger.info("[AUDITORIA] user_id=%s acao=%s ip=%s", user_id, acao, ip_origem)
