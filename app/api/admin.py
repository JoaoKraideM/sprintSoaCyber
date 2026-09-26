from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import obter_db, verificar_rbac
from app.services.admin_service import AdminService
from app.services.retencao_service import RetencaoService
from app.schemas.schemas import AdminAlterarRoleInput, AdminCriarUsuarioInput
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["Administracao Segura"])


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def painel_administrativo(
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    return {"admin": {"id": token_data["user_id"], "nome": token_data["nome"], "email": token_data["email"]}, **AdminService.obter_dashboard(db)}


@router.get("/comparacoes/veiculos", status_code=status.HTTP_200_OK)
def comparar_veiculos_admin(
    veiculo_id_a: int = Query(..., ge=1),
    veiculo_id_b: int = Query(..., ge=1),
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    try:
        return AdminService.comparar_veiculos(db, veiculo_id_a, veiculo_id_b)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/retencao/expurgar", status_code=status.HTTP_200_OK)
def expurgar_dados_antigos(
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    resultado = RetencaoService.expurgar_dados_antigos(db)
    return {"status": "sucesso", "admin_id": token_data["user_id"], **resultado}


@router.get("/usuarios", status_code=status.HTTP_200_OK)
def listar_usuarios_admin(
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    return {"usuarios": AdminService.listar_usuarios(db)}


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
def criar_usuario_admin(
    dados: AdminCriarUsuarioInput,
    request: Request,
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    try:
        user = AuthService.cadastrar_utilizador_sem_senha(
            db, dados.email, dados.role, nome=dados.nome
        )
        token, expires_at = AuthService.criar_convite_senha(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    base = str(request.base_url).rstrip("/")
    return {
        "status": "sucesso",
        "usuario": {"id": user.id, "nome": user.nome, "email": user.email, "role": user.role},
        "convite": {
            "url": f"{base}/redefinir-senha?token={token}",
            "expira_em": expires_at.isoformat(),
            "uso": "unico",
            "observacao": "O token bruto nao e armazenado no banco. Em producao, envie este link por canal seguro ao usuario.",
        },
    }


@router.patch("/usuarios/{user_id}/role", status_code=status.HTTP_200_OK)
def alterar_role_usuario_admin(
    user_id: int,
    dados: AdminAlterarRoleInput,
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    user = AdminService.obter_usuario(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador nao encontrado.")

    nova_role = AuthService.normalizar_role(dados.role)
    if user.id == token_data["user_id"] and nova_role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O administrador atual nao pode remover a propria role admin.")

    user.role = nova_role
    user.update_date = __import__("datetime").date.today()
    db.commit()
    return {"status": "sucesso", "id": user.id, "email": user.email, "role": user.role}


@router.post("/usuarios/{user_id}/redefinir-senha", status_code=status.HTTP_200_OK)
def gerar_reset_senha_admin(
    user_id: int,
    request: Request,
    token_data: dict = Depends(verificar_rbac(["admin"])),
    db: Session = Depends(obter_db),
):
    user = AdminService.obter_usuario(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador nao encontrado.")
    if not user.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao e possivel redefinir senha de utilizador inativo.")

    token, expires_at = AuthService.criar_convite_senha(db, user)
    base = str(request.base_url).rstrip("/")
    return {
        "status": "sucesso",
        "email": user.email,
        "reset": {
            "url": f"{base}/redefinir-senha?token={token}",
            "expira_em": expires_at.isoformat(),
            "uso": "unico",
        },
    }
