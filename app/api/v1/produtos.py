from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.db.models import Categoria, Produto, Subcategoria, Time, Usuario, VariacaoProduto
from app.schemas.catalog import ProdutoResponse, ProdutoCreate, ProdutoUpdate
from app.core.security import require_admin

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
    current_user: Usuario = Depends(require_admin)
):
    dados_produto = produto_data.model_dump()
    if dados_produto.get("imagem_url"):
        dados_produto["imagem_capa"] = dados_produto["imagem_url"]
    if not dados_produto.get("imagem_capa"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Envie imagem_url ou imagem_capa antes de cadastrar o produto.",
        )
    variacoes = dados_produto.pop("variacoes", [])

    novo_produto = Produto(**dados_produto)
    novo_produto.variacoes = [
        VariacaoProduto(**variacao) for variacao in variacoes
    ]
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto


@router.patch("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(
    produto_id: int,
    produto_data: ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    dados = produto_data.model_dump(exclude_unset=True)
    variacoes = dados.pop("variacoes", None)
    if "imagem_url" in dados and dados["imagem_url"]:
        dados["imagem_capa"] = dados["imagem_url"]

    for campo, valor in dados.items():
        setattr(produto, campo, valor)

    if variacoes is not None:
        produto.variacoes.clear()
        produto.variacoes.extend(
            VariacaoProduto(**variacao) for variacao in variacoes
        )

    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )

    db.delete(produto)
    db.commit()