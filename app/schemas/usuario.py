from pydantic import AliasChoices, BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UsuarioCreate(BaseModel):
    nome: Optional[str] = None
    email: EmailStr
    senha: str = Field(validation_alias=AliasChoices("senha", "password"))

class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str = Field(validation_alias=AliasChoices("senha", "password"))
    perfil: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("perfil", "role", "tipo", "tipo_usuario"),
    )

class UsuarioResponse(BaseModel):
    id: int
    nome: Optional[str] = None
    email: EmailStr
    role: str
    perfil: str
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UsuarioResponse