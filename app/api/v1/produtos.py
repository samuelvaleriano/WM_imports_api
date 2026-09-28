from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Produto, Usuario
from app.schemas.catalog import ProdutoResponse, ProdutoCreate
from app.core.security import get_current_user

router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"]
)

@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).filter(Produto.ativo == True).all()

@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(
    produto_data: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    novo_produto = Produto(**produto_data.model_dump())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto