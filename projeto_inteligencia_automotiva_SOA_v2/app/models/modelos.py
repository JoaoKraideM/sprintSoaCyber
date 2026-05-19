from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from app.db.session import Base

class UtilizadorModel(Base):
    __tablename__ = "utilizadores"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    role = Column(String(20), default="usuario", nullable=False) # admin, analista, usuario
    ativo = Column(Boolean, default=True)

class VeiculoModel(Base):
    __tablename__ = "veiculos"
    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(50), index=True, nullable=False)
    modelo = Column(String(50), index=True, nullable=False)
    versao = Column(String(50), index=True, nullable=False)
    motorizacao = Column(String(100), default="não disponível")
    potencia = Column(String(50), default="não disponível")
    transmissao = Column(String(50), default="não disponível")
    tracao = Column(String(50), default="não disponível")
    preco_sugerido = Column(String(50), default="não disponível")
    pacote_equipamentos = Column(Text, default="{}") # Armazenamento JSON estruturado

class LogAuditoriaModel(Base):
    __tablename__ = "logs_auditoria"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    utilizador = Column(String(50), index=True, nullable=True)
    acao = Column(String(100), nullable=False)
    detalhes = Column(Text, nullable=True)
    ip_origem = Column(String(45), nullable=True)