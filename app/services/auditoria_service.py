import logging

from sqlalchemy.orm import Session

from app.models.modelos import LogModel

logger = logging.getLogger("AuditoriaService")


class AuditoriaService:
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
        """Registra eventos sem depender do dominio de metricas."""
        log = LogModel(
            metrica_veiculo_id=metrica_veiculo_id,
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
