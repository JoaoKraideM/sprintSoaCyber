from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship

from app.db.session import Base


def _hora_atual_utc():
    return datetime.now(timezone.utc).time().replace(microsecond=0)


BIGINT_ID = BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql").with_variant(Integer, "sqlite")


class AuditColumnsMixin:
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(Time, nullable=False, default=_hora_atual_utc)
    update_date = Column(Date, nullable=True)
    update_hour = Column(Time, nullable=True)


class UserModel(AuditColumnsMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uk_users_email"),
        Index("idx_users_role", "role"),
        Index("idx_users_status", "status"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="user")
    status = Column(Boolean, nullable=False, default=True)

    metricas = relationship("MetricaVeiculoModel", back_populates="user")
    logs = relationship("LogModel", back_populates="user")
    logs_auth = relationship("LogAuthModel", back_populates="user")


class MarcaModel(AuditColumnsMixin, Base):
    __tablename__ = "marcas"
    __table_args__ = (UniqueConstraint("nome", name="uk_marcas_nome"),)

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)

    modelos = relationship("ModeloModel", back_populates="marca")


class ModeloModel(AuditColumnsMixin, Base):
    __tablename__ = "modelos"
    __table_args__ = (
        UniqueConstraint("marca_id", "nome", name="uk_modelos_marca_nome"),
        Index("idx_modelos_marca_id", "marca_id"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    marca_id = Column(BIGINT_ID, ForeignKey("marcas.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)

    marca = relationship("MarcaModel", back_populates="modelos")
    versoes = relationship("VersaoModel", back_populates="modelo")


class VersaoModel(AuditColumnsMixin, Base):
    __tablename__ = "versoes"
    __table_args__ = (
        UniqueConstraint("modelo_id", "nome", name="uk_versoes_modelo_nome"),
        Index("idx_versoes_modelo_id", "modelo_id"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    modelo_id = Column(BIGINT_ID, ForeignKey("modelos.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)

    modelo = relationship("ModeloModel", back_populates="versoes")
    veiculos = relationship("VeiculoModel", back_populates="versao")


class VeiculoModel(AuditColumnsMixin, Base):
    __tablename__ = "veiculos"
    __table_args__ = (
        Index("idx_veiculos_versao_id", "versao_id"),
        Index("idx_veiculos_status", "status"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    versao_id = Column(BIGINT_ID, ForeignKey("versoes.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    motorizacao = Column(String(100), nullable=False)
    potencia_cv = Column(Integer, nullable=False)
    transmissao = Column(String(50), nullable=False)
    tracao = Column(String(50), nullable=False)
    status = Column(Boolean, nullable=False, default=True)

    versao = relationship("VersaoModel", back_populates="veiculos")
    metricas = relationship("MetricaVeiculoModel", back_populates="veiculo")


class MetricaVeiculoModel(AuditColumnsMixin, Base):
    __tablename__ = "metricas_veiculos"
    __table_args__ = (
        Index("idx_metricas_veiculos_veiculo_id", "veiculo_id"),
        Index("idx_metricas_veiculos_user_id", "user_id"),
        Index("idx_metricas_veiculos_create_date", "create_date"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    veiculo_id = Column(BIGINT_ID, ForeignKey("veiculos.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    preco_sugerido = Column(Numeric(12, 2), nullable=True)
    pacote_equipamentos = Column(JSON, nullable=True)
    observacao = Column(String(120), nullable=True)

    veiculo = relationship("VeiculoModel", back_populates="metricas")
    user = relationship("UserModel", back_populates="metricas")
    logs = relationship("LogModel", back_populates="metrica")


class LogModel(AuditColumnsMixin, Base):
    __tablename__ = "logs"
    __table_args__ = (
        Index("idx_logs_metrica_veiculo_id", "metrica_veiculo_id"),
        Index("idx_logs_user_id", "user_id"),
        Index("idx_logs_acao", "acao"),
        Index("idx_logs_create_date", "create_date"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    metrica_veiculo_id = Column(
        BIGINT_ID,
        ForeignKey("metricas_veiculos.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    acao = Column(String(50), nullable=False)
    dados_antes = Column(JSON, nullable=True)
    dados_depois = Column(JSON, nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    metrica = relationship("MetricaVeiculoModel", back_populates="logs")
    user = relationship("UserModel", back_populates="logs")


class LogAuthModel(Base):
    __tablename__ = "logs_auth"
    __table_args__ = (
        Index("idx_logs_auth_user_id", "user_id"),
        Index("idx_logs_auth_address", "address"),
        Index("idx_logs_auth_ip", "ip"),
        Index("idx_logs_auth_status", "status"),
        Index("idx_logs_auth_create_date", "create_date"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    user_agent = Column(String(255), nullable=True)
    address = Column(String(100), nullable=True)
    ip = Column(String(45), nullable=True)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(Time, nullable=False, default=_hora_atual_utc)
    expires_at = Column(DateTime, nullable=True)
    status = Column(Boolean, nullable=False, default=False)

    user = relationship("UserModel", back_populates="logs_auth")


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("idx_password_reset_tokens_user_id", "user_id"),
        Index("idx_password_reset_tokens_token", "token"),
        Index("idx_password_reset_tokens_expires_at", "expires_at"),
    )

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    token = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    create_at = Column(Date, nullable=False, default=date.today)
    hour_date = Column(Time, nullable=False, default=_hora_atual_utc)
