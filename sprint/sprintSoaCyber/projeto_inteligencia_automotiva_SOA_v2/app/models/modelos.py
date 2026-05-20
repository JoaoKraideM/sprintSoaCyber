from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db.session import Base


class UtilizadorModel(Base):
    __tablename__ = "utilizadores"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="usuario", nullable=False)  # admin, analista, usuario
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class VeiculoModel(Base):
    __tablename__ = "veiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(50), index=True, nullable=False)
    modelo = Column(String(50), index=True, nullable=False)
    versao = Column(String(50), index=True, nullable=False)
    motorizacao = Column(String(100), default="nao disponivel")
    potencia = Column(String(50), default="nao disponivel")
    transmissao = Column(String(50), default="nao disponivel")
    tracao = Column(String(50), default="nao disponivel")
    preco_sugerido = Column(String(50), default="nao disponivel")
    pacote_equipamentos = Column(Text, default="{}")  # armazenamento JSON estruturado


class LogAuditoriaModel(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    utilizador = Column(String(120), index=True, nullable=True)
    acao = Column(String(100), nullable=False)
    detalhes = Column(Text, nullable=True)
    ip_origem = Column(String(45), nullable=True)


class LogUploadModel(Base):
    __tablename__ = "logs_upload"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    utilizador_email = Column(String(120), index=True, nullable=False)
    nome_original = Column(String(255), nullable=False)
    nome_armazenado = Column(String(255), nullable=False)
    caminho_armazenado = Column(String(500), nullable=False)
    tamanho_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(120), nullable=False)
    status_upload = Column(String(20), default="sucesso", nullable=False)
