from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.db.models import Categoria, Produto, Subcategoria, Time, Usuario
from app.schemas.catalog import ProdutoResponse, ProdutoCreate
from app.core.security import get_current_user

router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"]
)

@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(
    categoria: Optional[str] = Query(None, description="Slug ou nome da categoria"),
    subcategoria: Optional[str] = Query(None, description="Slug ou nome da subcategoria"),
    time: Optional[str] = Query(None, description="Slug ou nome do time"),
    busca: Optional[str] = Query(None, description="Termo digitado na barra de pesquisa"),
    db: Session = Depends(get_db)
):
    query = db.query(Produto).filter(Produto.ativo == True)

    if any(valor and valor.strip() for valor in (categoria, subcategoria, time)):
        query = query.join(Produto.time).join(Time.subcategoria).join(Subcategoria.categoria)

    if categoria and categoria.strip():
        valor_categoria = categoria.strip()
        query = query.filter(
            or_(
                Categoria.slug == valor_categoria,
                Categoria.nome.ilike(valor_categoria)
            )
        )

    if subcategoria and subcategoria.strip():
        valor_subcategoria = subcategoria.strip()
        query = query.filter(
            or_(
                Subcategoria.slug == valor_subcategoria,
                Subcategoria.nome.ilike(valor_subcategoria)
            )
        )

    if time and time.strip():
        valor_time = time.strip()
        query = query.filter(
            or_(
                Time.slug == valor_time,
                Time.nome.ilike(valor_time)
            )
        )

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Produto.nome.ilike(termo),
                Produto.descricao.ilike(termo)
            )
        )

    return query.all()

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