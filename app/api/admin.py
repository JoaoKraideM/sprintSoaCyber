from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db, verificar_rbac
from app.services.retencao_service import RetencaoService

router = APIRouter(prefix="/admin", tags=["Administracao Segura"])


@router.post("/retencao/expurgar", status_code=status.HTTP_200_OK)
def expurgar_dados_antigos(
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    resultado = RetencaoService.expurgar_dados_antigos(db)
    return {"status": "sucesso", "admin_id": token_data["user_id"], **resultado}
