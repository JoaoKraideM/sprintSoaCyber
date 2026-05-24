from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.services.auditoria_service import AuditoriaService


@dataclass(frozen=True)
class EventoDominio:
    nome: str
    user_id: int
    dados_depois: dict[str, Any] = field(default_factory=dict)
    dados_antes: dict[str, Any] | None = None
    metrica_veiculo_id: int | None = None
    ip_origem: str | None = None
    user_agent: str | None = None


class EventBus:
    """Publicador simples para desacoplar servicos de negocio da auditoria."""

    @staticmethod
    def publicar(db: Session, evento: EventoDominio) -> None:
        AuditoriaService.registar_evento(
            db=db,
            user_id=evento.user_id,
            acao=evento.nome,
            ip_origem=evento.ip_origem,
            user_agent=evento.user_agent,
            metrica_veiculo_id=evento.metrica_veiculo_id,
            dados_antes=evento.dados_antes,
            dados_depois=evento.dados_depois,
        )
