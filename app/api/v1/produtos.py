from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Produto
from app.schemas.catalog import ProdutoResponse

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).filter(Produto.ativo == True).all()