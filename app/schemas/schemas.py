from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.security import normalizar_email, sanitizar_string, validar_forca_senha


class CadastroUsuarioInput(BaseModel):
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=8, max_length=120)
    role: str = Field(default="usuario", max_length=20)

    @field_validator("email", mode="before")
    @classmethod
    def validar_email(cls, v):
        return normalizar_email(v)

    @field_validator("password")
    @classmethod
    def validar_password(cls, v):
        validar_forca_senha(v)
        return v

    @field_validator("role", mode="before")
    @classmethod
    def validar_role(cls, v):
        role = sanitizar_string(v).lower()
        if role not in {"admin", "analista", "usuario"}:
            raise ValueError("Role invalida.")
        return role


class LoginInput(BaseModel):
    email: Optional[str] = Field(default=None, max_length=120)
    username: Optional[str] = Field(default=None, max_length=120)
    password: str = Field(..., min_length=8, max_length=120)

    @model_validator(mode="after")
    def validar_identificador(self):
        identificador = self.email or self.username
        if not identificador:
            raise ValueError("Informe email ou username para login.")

        self.email = normalizar_email(identificador)
        if self.username:
            self.username = sanitizar_string(self.username)

        validar_forca_senha(self.password)
        return self


class ConsultaVeiculoInput(BaseModel):
    marca: str = Field(..., max_length=50)
    modelo: str = Field(..., max_length=50)
    versao: str = Field(..., max_length=50)
    atributos_desejados: List[str] = Field(default_factory=list, max_length=20)

    @field_validator("marca", "modelo", "versao", mode="before")
    @classmethod
    def validar_strings(cls, v):
        return sanitizar_string(v)

    @field_validator("atributos_desejados", mode="before")
    @classmethod
    def validar_lista(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("atributos_desejados deve ser lista.")
        return [sanitizar_string(item) for item in v]


class CadastroVeiculoInput(BaseModel):
    marca: str = Field(..., max_length=50)
    modelo: str = Field(..., max_length=50)
    versao: str = Field(..., max_length=50)
    motorizacao: Optional[str] = "nao disponivel"
    potencia: Optional[str] = "nao disponivel"
    transmissao: Optional[str] = "nao disponivel"
    tracao: Optional[str] = "nao disponivel"
    preco_sugerido: Optional[str] = "nao disponivel"
    pacote_equipamentos: Dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "marca",
        "modelo",
        "versao",
        "motorizacao",
        "potencia",
        "transmissao",
        "tracao",
        "preco_sugerido",
        mode="before",
    )
    @classmethod
    def sanitizar_campos(cls, v):
        if v is None:
            return v
        return sanitizar_string(v)


class UploadArquivoResposta(BaseModel):
    status: str
    mensagem: str
    caminho_arquivo: str
    nome_arquivo: str
