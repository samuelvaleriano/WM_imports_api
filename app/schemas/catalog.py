from pydantic import BaseModel, Field
from typing import List, Optional
from app.db.models import TamanhoEnum

class VariacaoBase(BaseModel):
    tamanho: TamanhoEnum
    estoque: int

class VariacaoCreate(VariacaoBase):
    pass

class VariacaoResponse(VariacaoBase):
    id: int
    produto_id: int

    class Config:
        from_attributes = True

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    desconto_percentual: float = Field(default=0, ge=0, le=100)
    imagem_capa: Optional[str] = None
    imagem_url: Optional[str] = None
    ativo: bool = True

class ProdutoCreate(ProdutoBase):
    time_id: int
    variacoes: List[VariacaoCreate] = []

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    desconto_percentual: Optional[float] = Field(default=None, ge=0, le=100)
    imagem_capa: Optional[str] = None
    imagem_url: Optional[str] = None
    ativo: Optional[bool] = None
    time_id: Optional[int] = None
    variacoes: Optional[List[VariacaoCreate]] = None

class ProdutoResponse(ProdutoBase):
    id: int
    time_id: int
    variacoes: List[VariacaoResponse] = []

    class Config:
        from_attributes = True

class CategoriaBase(BaseModel):
    nome: str
    slug: str

class CategoriaResponse(CategoriaBase):
    id: int

    class Config:
        from_attributes = True