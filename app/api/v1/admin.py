from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_admin
from app.db.database import get_db
from app.db.models import Categoria, Produto, Usuario, VariacaoProduto
from app.schemas.usuario import UsuarioCreate, UsuarioResponse

router = APIRouter(
    prefix="/admin",
    tags=["Administração"],
)


@router.post("/users", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_lojista(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    usuario_existente = (
        db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    )
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado no sistema.",
        )

    lojista = Usuario(
        nome=usuario_data.nome,
        email=usuario_data.email,
        hashed_password=hash_password(usuario_data.senha),
        role="admin",
    )
    db.add(lojista)
    db.commit()
    db.refresh(lojista)
    return lojista


@router.get("/dashboard/stats")
def obter_estatisticas_dashboard(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    total_produtos = db.query(func.count(Produto.id)).scalar() or 0
    produtos_ativos = (
        db.query(func.count(Produto.id))
        .filter(Produto.ativo.is_(True))
        .scalar()
        or 0
    )
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    total_categorias = db.query(func.count(Categoria.id)).scalar() or 0
    estoque_total = db.query(func.coalesce(func.sum(VariacaoProduto.estoque), 0)).scalar() or 0
    produtos_estoque_baixo = (
        db.query(func.count(func.distinct(VariacaoProduto.produto_id)))
        .filter(VariacaoProduto.estoque <= 5)
        .scalar()
        or 0
    )

    return {
        "totalProducts": total_produtos,
        "activeProducts": produtos_ativos,
        "totalUsers": total_usuarios,
        "totalCategories": total_categorias,
        "totalStock": estoque_total,
        "lowStockProducts": produtos_estoque_baixo,
    }
