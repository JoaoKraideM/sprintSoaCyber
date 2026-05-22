from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db, verificar_rbac
from app.schemas.schemas import ProcessamentoExcelResposta, UploadArquivoResposta
from app.services.auditoria_service import AuditoriaService
from app.services.upload_service import ImportacaoExcelError, UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads Excel"])


@router.post("/excel", response_model=UploadArquivoResposta, status_code=status.HTTP_201_CREATED)
async def upload_excel(
    request: Request,
    arquivo: UploadFile = File(...),
    token_data: dict = Depends(verificar_rbac(["admin", "analista", "user"])),
    db: Session = Depends(obter_db),
):
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    try:
        resultado = await UploadService.processar_upload_excel(
            db,
            user_id=token_data["user_id"],
            user_email=token_data["email"],
            arquivo=arquivo,
            ip_origem=ip,
            user_agent=user_agent,
        )
    except ValueError as exc:
        AuditoriaService.registar_evento(
            db,
            user_id=token_data["user_id"],
            acao="FALHA_UPLOAD_EXCEL",
            ip_origem=ip,
            user_agent=user_agent,
            dados_depois={"erro": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return resultado


@router.post("/excel/processar", response_model=ProcessamentoExcelResposta, status_code=status.HTTP_201_CREATED)
async def processar_excel(
    request: Request,
    arquivo: UploadFile = File(...),
    token_data: dict = Depends(verificar_rbac(["admin", "analista"])),
    db: Session = Depends(obter_db),
):
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    try:
        return await UploadService.processar_importacao_excel(
            db=db,
            user_id=token_data["user_id"],
            arquivo=arquivo,
            ip_origem=ip,
            user_agent=user_agent,
        )
    except ImportacaoExcelError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"mensagem": exc.mensagem, "erros_validacao": exc.erros_validacao},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"mensagem": str(exc), "erros_validacao": [str(exc)]},
        ) from exc
