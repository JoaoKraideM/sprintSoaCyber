import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.modelos import LogModel, MetricaVeiculoModel

_FILENAME_REGEX = re.compile(r"[^A-Za-z0-9._-]")


class UploadService:
    @staticmethod
    def _upload_dir_seguro() -> Path:
        raiz_projeto = Path(__file__).resolve().parents[2]
        upload_dir = Path(settings.UPLOAD_DIR)
        if not upload_dir.is_absolute():
            upload_dir = (raiz_projeto / upload_dir).resolve()

        raiz_resolvida = raiz_projeto.resolve()
        if raiz_resolvida not in upload_dir.parents and upload_dir != raiz_resolvida:
            raise ValueError("Diretorio de upload fora da raiz do projeto.")

        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @staticmethod
    def _nome_seguro(nome_original: str) -> str:
        nome = Path(nome_original or "").name
        nome = _FILENAME_REGEX.sub("_", nome).strip("._")
        if not nome:
            raise ValueError("Nome de arquivo invalido.")
        return nome

    @staticmethod
    def _validar_tipo_arquivo(nome: str, mime_type: str) -> str:
        extensao = Path(nome).suffix.lower()
        extensoes_permitidas = {ext.lower() for ext in settings.ALLOWED_UPLOAD_EXTENSIONS}
        mimes_permitidos = {mime.lower() for mime in settings.ALLOWED_UPLOAD_CONTENT_TYPES}

        if extensao not in extensoes_permitidas:
            raise ValueError("Somente arquivos Excel (.xlsx ou .xls) sao permitidos.")

        mime = (mime_type or "application/octet-stream").lower()
        if mime not in mimes_permitidos:
            raise ValueError("Tipo MIME nao permitido para upload.")

        return extensao

    @staticmethod
    def _obter_metrica_para_log(db: Session, user_id: int) -> int | None:
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
    async def processar_upload_excel(
        db: Session,
        user_id: int,
        user_email: str,
        arquivo: UploadFile,
        ip_origem: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        nome_original = UploadService._nome_seguro(arquivo.filename)
        extensao = UploadService._validar_tipo_arquivo(nome_original, arquivo.content_type)

        conteudo = await arquivo.read()
        tamanho = len(conteudo)
        if tamanho == 0:
            raise ValueError("Arquivo vazio nao permitido.")
        if tamanho > settings.MAX_UPLOAD_FILE_SIZE:
            raise ValueError("Arquivo excede o tamanho maximo permitido.")

        upload_dir = UploadService._upload_dir_seguro()
        nome_armazenado = f"{uuid.uuid4().hex}{extensao}"
        caminho_arquivo = upload_dir / nome_armazenado
        caminho_arquivo.write_bytes(conteudo)

        metrica_id = UploadService._obter_metrica_para_log(db, user_id)

        if metrica_id:
            log = LogModel(
                metrica_veiculo_id=metrica_id,
                user_id=user_id,
                acao="UPLOAD_EXCEL",
                dados_antes=None,
                dados_depois={
                    "email": user_email,
                    "nome_original": nome_original,
                    "nome_armazenado": nome_armazenado,
                    "caminho_armazenado": str(caminho_arquivo),
                    "tamanho_bytes": tamanho,
                    "mime_type": arquivo.content_type or "application/octet-stream",
                },
                ip=ip_origem,
                user_agent=(user_agent or "")[0:255] or None,
            )
            db.add(log)
            db.commit()

        return {
            "status": "sucesso",
            "mensagem": "Upload realizado com sucesso.",
            "caminho_arquivo": str(caminho_arquivo),
            "nome_arquivo": nome_original,
            "metrica_id": metrica_id,
        }
