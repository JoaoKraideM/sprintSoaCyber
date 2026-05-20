import logging
from sqlalchemy.orm import Session
from app.models.modelos import LogAuditoriaModel

logger = logging.getLogger("AuditoriaService")

class AuditoriaService:
    @staticmethod
    def registar_evento(db: Session, utilizador: str, acao: str, detalhes: str, ip_origem: str):
        """Serviço Reutilizável de Auditoria de Cybersecurity"""
        log = LogAuditoriaModel(
            utilizador=utilizador,
            acao=acao,
            detalhes=detalhes,
            ip_origem=ip_origem
        )
        db.add(log)
        db.commit()
        logger.info(f"[AUDITORIA] {utilizador} realizou {acao} de IP {ip_origem}")