from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UsuarioCreate(BaseModel):
    nome: Optional[str] = None
    email: EmailStr
    senha: str

class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

    
class UsuarioResponse(BaseModel):
    id: int
    nome: Optional[str] = None
    email: EmailStr
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True