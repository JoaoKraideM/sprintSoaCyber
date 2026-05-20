from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db, verificar_rbac
from app.schemas.schemas import UploadArquivoResposta
from app.services.auditoria_service import AuditoriaService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads Excel"])


@router.post("/excel", response_model=UploadArquivoResposta, status_code=status.HTTP_201_CREATED)
async def upload_excel(
    request: Request,
    arquivo: UploadFile = File(...),
    token_data: dict = Depends(verificar_rbac(["admin", "analista", "usuario"])),
    db: Session = Depends(obter_db),
):
    ip = request.client.host if request.client else "127.0.0.1"

    try:
        resultado = await UploadService.processar_upload_excel(db, token_data["email"], arquivo)
    except ValueError as exc:
        AuditoriaService.registar_evento(
            db,
            token_data["email"],
            "FALHA_UPLOAD_EXCEL",
            f"Upload recusado: {str(exc)}",
            ip,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    AuditoriaService.registar_evento(
        db,
        token_data["email"],
        "SUCESSO_UPLOAD_EXCEL",
        f"Arquivo recebido: {resultado['nome_arquivo']}",
        ip,
    )

    return resultado
