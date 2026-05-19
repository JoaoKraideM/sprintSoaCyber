from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from app.core.security import sanitizar_string

class LoginInput(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=100)

    @validator("username", pre=True)
    def validar_username(cls, v): return sanitizar_string(v)

class ConsultaVeiculoInput(BaseModel):
    marca: str = Field(..., max_length=50)
    modelo: str = Field(..., max_length=50)
    versao: str = Field(..., max_length=50)
    atributos_desejados: List[str] = Field(default=[], max_length=20)

    @validator("marca", "modelo", "versao", pre=True)
    def validar_strings(cls, v): return sanitizar_string(v)

    @validator("atributos_desejados", pre=True, each_item=True)
    def validar_lista(cls, v): return sanitizar_string(v)

class CadastroVeiculoInput(BaseModel):
    marca: str = Field(..., max_length=50)
    modelo: str = Field(..., max_length=50)
    versao: str = Field(..., max_length=50)
    motorizacao: Optional[str] = "não disponível"
    potencia: Optional[str] = "não disponível"
    transmissao: Optional[str] = "não disponível"
    tracao: Optional[str] = "não disponível"
    preco_sugerido: Optional[str] = "não disponível"
    pacote_equipamentos: Dict[str, Any] = {}