from pydantic import BaseModel
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
    imagem_capa: str
    ativo: bool = True

class ProdutoCreate(ProdutoBase):
    time_id: int
    variacoes: List[VariacaoCreate] = []

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