from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.modelos import (
    LogAuthModel,
    LogModel,
    MarcaModel,
    MetricaVeiculoModel,
    ModeloModel,
    UserModel,
    VeiculoModel,
    VersaoModel,
)


class AdminService:
    @staticmethod
    def listar_usuarios(db: Session) -> list[dict]:
        usuarios = db.query(UserModel).order_by(UserModel.id.desc()).all()
        return [
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "role": u.role,
                "status": bool(u.status),
                "create_date": u.create_date.isoformat() if u.create_date else None,
            }
            for u in usuarios
        ]

    @staticmethod
    def obter_usuario(db: Session, user_id: int) -> UserModel | None:
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    """Consultas administrativas e indicadores para o painel do administrador."""

    @staticmethod
    def obter_dashboard(db: Session) -> dict:
        usuarios = db.query(func.count(UserModel.id)).scalar() or 0
        usuarios_ativos = db.query(func.count(UserModel.id)).filter(UserModel.status.is_(True)).scalar() or 0
        admins = db.query(func.count(UserModel.id)).filter(UserModel.role == "admin", UserModel.status.is_(True)).scalar() or 0
        analistas = db.query(func.count(UserModel.id)).filter(UserModel.role == "analista", UserModel.status.is_(True)).scalar() or 0
        usuarios_comuns = db.query(func.count(UserModel.id)).filter(UserModel.role == "user", UserModel.status.is_(True)).scalar() or 0
        veiculos_ativos = db.query(func.count(VeiculoModel.id)).filter(VeiculoModel.status.is_(True)).scalar() or 0
        marcas = db.query(func.count(MarcaModel.id)).scalar() or 0
        modelos = db.query(func.count(ModeloModel.id)).scalar() or 0
        versoes = db.query(func.count(VersaoModel.id)).scalar() or 0
        metricas = db.query(func.count(MetricaVeiculoModel.id)).scalar() or 0
        logs = db.query(func.count(LogModel.id)).scalar() or 0
        logins = db.query(func.count(LogAuthModel.id)).scalar() or 0
        logins_sucesso = db.query(func.count(LogAuthModel.id)).filter(LogAuthModel.status.is_(True)).scalar() or 0
        logins_falha = db.query(func.count(LogAuthModel.id)).filter(LogAuthModel.status.is_(False)).scalar() or 0

        return {
            "usuarios": {
                "total": usuarios,
                "ativos": usuarios_ativos,
                "admins": admins,
                "analistas": analistas,
                "usuarios": usuarios_comuns,
            },
            "catalogo": {
                "veiculos_ativos": veiculos_ativos,
                "marcas": marcas,
                "modelos": modelos,
                "versoes": versoes,
                "metricas": metricas,
            },
            "auditoria": {
                "logs": logs,
                "tentativas_login": logins,
                "login_sucesso": logins_sucesso,
                "login_falha": logins_falha,
            },
            "sprint3": {
                "pipeline_devsecops": [
                    {"item": "SAST", "status": "implementado/documentado"},
                    {"item": "SCA", "status": "implementado/documentado"},
                    {"item": "Secret Scanning", "status": "configurado no projeto"},
                    {"item": "Container Security", "status": "planejado/documentado"},
                ],
                "seguranca_codigo_infra": [
                    {"item": "JWT + RBAC", "status": "ativo"},
                    {"item": "Validacao de entrada", "status": "ativa"},
                    {"item": "Assinatura HMAC de payload", "status": "ativa/configuravel"},
                    {"item": "TLS local", "status": "documentado"},
                ],
                "observabilidade": [
                    {"item": "Logs de autenticacao", "status": "ativo", "quantidade": logins},
                    {"item": "Logs de auditoria", "status": "ativo", "quantidade": logs},
                    {"item": "Health check do banco", "status": "ativo"},
                ],
                "compliance": [
                    {"item": "OWASP API Top 10", "status": "mapeado"},
                    {"item": "LGPD / minimizacao e pseudonimizacao", "status": "implementado"},
                    {"item": "Retencao de dados", "status": "disponivel para admin"},
                ],
            },
        }

    @staticmethod
    def _veiculo_completo(db: Session, veiculo_id: int):
        return (
            db.query(VeiculoModel, MarcaModel.nome, ModeloModel.nome, VersaoModel.nome)
            .join(VersaoModel, VeiculoModel.versao_id == VersaoModel.id)
            .join(ModeloModel, VersaoModel.modelo_id == ModeloModel.id)
            .join(MarcaModel, ModeloModel.marca_id == MarcaModel.id)
            .filter(VeiculoModel.id == veiculo_id)
            .first()
        )

    @staticmethod
    def _ultima_metrica(db: Session, veiculo_id: int):
        return (
            db.query(MetricaVeiculoModel)
            .filter(MetricaVeiculoModel.veiculo_id == veiculo_id)
            .order_by(
                MetricaVeiculoModel.create_date.desc(),
                MetricaVeiculoModel.hour_date.desc(),
                MetricaVeiculoModel.id.desc(),
            )
            .first()
        )

    @staticmethod
    def comparar_veiculos(db: Session, veiculo_id_a: int, veiculo_id_b: int) -> dict:
        if veiculo_id_a == veiculo_id_b:
            raise ValueError("Informe dois veiculos diferentes para comparacao.")

        registro_a = AdminService._veiculo_completo(db, veiculo_id_a)
        registro_b = AdminService._veiculo_completo(db, veiculo_id_b)
        if not registro_a or not registro_b:
            raise LookupError("Um ou ambos os veiculos nao foram encontrados.")

        def montar(registro):
            veiculo, marca, modelo, versao = registro
            metrica = AdminService._ultima_metrica(db, veiculo.id)
            return {
                "id": veiculo.id,
                "marca": marca,
                "modelo": modelo,
                "versao": versao,
                "motorizacao": veiculo.motorizacao,
                "potencia_cv": veiculo.potencia_cv,
                "transmissao": veiculo.transmissao,
                "tracao": veiculo.tracao,
                "preco_sugerido": float(metrica.preco_sugerido) if metrica and metrica.preco_sugerido is not None else None,
                "pacote_equipamentos": metrica.pacote_equipamentos if metrica else {},
                "observacao": metrica.observacao if metrica else None,
                "ativo": bool(veiculo.status),
            }

        a = montar(registro_a)
        b = montar(registro_b)

        campos_numericos = ["potencia_cv", "preco_sugerido"]
        diferencas = {}
        for campo in campos_numericos:
            valor_a = a[campo]
            valor_b = b[campo]
            diferencas[campo] = {
                "veiculo_a": valor_a,
                "veiculo_b": valor_b,
                "diferenca": (valor_a - valor_b) if valor_a is not None and valor_b is not None else None,
            }

        return {
            "veiculo_a": a,
            "veiculo_b": b,
            "diferencas_numericas": diferencas,
            "mesma_marca": a["marca"] == b["marca"],
            "mesmo_modelo": a["modelo"] == b["modelo"],
        }
