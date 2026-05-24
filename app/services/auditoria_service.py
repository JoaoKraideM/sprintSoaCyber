import logging

from sqlalchemy.orm import Session

from app.core.privacy import sanitizar_para_auditoria
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
            dados_antes=sanitizar_para_auditoria(dados_antes),
            dados_depois=sanitizar_para_auditoria(dados_depois),
            ip=sanitizar_para_auditoria(ip_origem, "ip"),
            user_agent=sanitizar_para_auditoria((user_agent or "")[0:255], "user_agent") or None,
        )
        db.add(log)
        db.commit()
        logger.info("[AUDITORIA] user_id=%s acao=%s ip=%s", user_id, acao, ip_origem)
