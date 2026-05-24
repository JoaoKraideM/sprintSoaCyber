from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.modelos import LogAuthModel, LogModel, PasswordResetTokenModel


class RetencaoService:
    @staticmethod
    def expurgar_dados_antigos(db: Session) -> dict:
        limite_logs = date.today() - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
        limite_auth = date.today() - timedelta(days=settings.AUTH_LOG_RETENTION_DAYS)
        agora = datetime.now(timezone.utc)

        logs_removidos = db.query(LogModel).filter(LogModel.create_date < limite_logs).delete(
            synchronize_session=False
        )
        logs_auth_removidos = db.query(LogAuthModel).filter(LogAuthModel.create_date < limite_auth).delete(
            synchronize_session=False
        )
        tokens_expirados = db.query(PasswordResetTokenModel).filter(PasswordResetTokenModel.expires_at < agora).delete(
            synchronize_session=False
        )
        db.commit()

        uploads_removidos = RetencaoService.expurgar_uploads_antigos()
        return {
            "logs_removidos": logs_removidos,
            "logs_auth_removidos": logs_auth_removidos,
            "tokens_expirados_removidos": tokens_expirados,
            "uploads_removidos": uploads_removidos,
        }

    @staticmethod
    def expurgar_uploads_antigos() -> int:
        upload_dir = Path(settings.UPLOAD_DIR)
        if not upload_dir.is_absolute():
            upload_dir = (Path(__file__).resolve().parents[2] / upload_dir).resolve()
        if not upload_dir.exists() or not upload_dir.is_dir():
            return 0

        limite_timestamp = datetime.now(timezone.utc).timestamp() - (settings.UPLOAD_RETENTION_DAYS * 24 * 60 * 60)
        removidos = 0
        for arquivo in upload_dir.iterdir():
            if not arquivo.is_file():
                continue
            if arquivo.stat().st_mtime >= limite_timestamp:
                continue
            arquivo.unlink(missing_ok=True)
            removidos += 1
        return removidos
