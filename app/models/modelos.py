from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship

from app.db.session import Base


BIGINT_ID = BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql").with_variant(Integer, "sqlite")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="user")
    status = Column(Boolean, nullable=False, default=True)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    metricas = relationship("MetricaVeiculoModel", back_populates="user")
    logs = relationship("LogModel", back_populates="user")


class ModeloModel(Base):
    __tablename__ = "modelos"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    marca = Column(String(100), nullable=False)
    nome = Column(String(100), nullable=False)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    versoes = relationship("VersaoModel", back_populates="modelo")


class VersaoModel(Base):
    __tablename__ = "versoes"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    modelo_id = Column(BIGINT_ID, ForeignKey("modelos.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    modelo = relationship("ModeloModel", back_populates="versoes")
    veiculos = relationship("VeiculoModel", back_populates="versao")


class VeiculoModel(Base):
    __tablename__ = "veiculos"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    versao_id = Column(BIGINT_ID, ForeignKey("versoes.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    motorizacao = Column(String(100), nullable=False)
    potencia_cv = Column(Integer, nullable=False)
    transmissao = Column(String(50), nullable=False)
    tracao = Column(String(50), nullable=False)
    status = Column(Boolean, nullable=False, default=True)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    versao = relationship("VersaoModel", back_populates="veiculos")
    metricas = relationship("MetricaVeiculoModel", back_populates="veiculo")


class MetricaVeiculoModel(Base):
    __tablename__ = "metricas_veiculos"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    veiculo_id = Column(BIGINT_ID, ForeignKey("veiculos.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    preco_sugerido = Column(Numeric(12, 2), nullable=False)
    pacote_equipamentos = Column(JSON, nullable=True)
    observacao = Column(String(120), nullable=True)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    veiculo = relationship("VeiculoModel", back_populates="metricas")
    user = relationship("UserModel", back_populates="metricas")
    logs = relationship("LogModel", back_populates="metrica")


class LogModel(Base):
    __tablename__ = "logs"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    metrica_veiculo_id = Column(
        BIGINT_ID,
        ForeignKey("metricas_veiculos.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    acao = Column(String(50), nullable=False)
    dados_antes = Column(JSON, nullable=True)
    dados_depois = Column(JSON, nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(50), nullable=True)
    create_date = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    metrica = relationship("MetricaVeiculoModel", back_populates="logs")
    user = relationship("UserModel", back_populates="logs")


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(BIGINT_ID, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BIGINT_ID, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    token = Column(String(255), nullable=False)
    expires_at = Column(Date, nullable=False)
    create_at = Column(Date, nullable=False, default=date.today)
    hour_date = Column(DateTime, nullable=False, default=datetime.utcnow)
