import logging

from sqlalchemy.orm import Session

from app.models.modelos import LogModel, MetricaVeiculoModel

logger = logging.getLogger("AuditoriaService")


class AuditoriaService:
    @staticmethod
    def _obter_metrica_existente(db: Session, user_id: int) -> int | None:
        metrica = (
            db.query(MetricaVeiculoModel)
            .filter(MetricaVeiculoModel.user_id == user_id)
            .order_by(
                MetricaVeiculoModel.create_date.desc(),
                MetricaVeiculoModel.hour_date.desc(),
                MetricaVeiculoModel.id.desc(),
            )
            .first()
        )
        return metrica.id if metrica else None

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
        """Registra eventos na tabela logs sem criar dados auxiliares no banco."""
        metrica_id = metrica_veiculo_id or AuditoriaService._obter_metrica_existente(db, user_id)
        if not metrica_id:
            logger.info(
                "[AUDITORIA] evento ignorado por falta de metrica vinculada: user_id=%s acao=%s",
                user_id,
                acao,
            )
            return

        log = LogModel(
            metrica_veiculo_id=metrica_id,
            user_id=user_id,
            acao=(acao or "ACAO")[0:50],
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            ip=ip_origem,
            user_agent=(user_agent or "")[0:255] or None,
        )
        db.add(log)
        db.commit()
        logger.info("[AUDITORIA] user_id=%s acao=%s ip=%s", user_id, acao, ip_origem)
