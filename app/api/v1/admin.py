import os
from pathlib import PurePosixPath
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_admin
from app.db.database import get_db
from app.db.models import (
    Categoria,
    HeroBanner,
    Produto,
    Subcategoria,
    Time,
    Usuario,
    VariacaoProduto,
)
from app.schemas.admin import AtualizarBanners, HeroBannerResponse
from app.schemas.usuario import UsuarioCreate, UsuarioResponse

router = APIRouter(
    prefix="/admin",
    tags=["Administração"],
)

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/png": ".png", "image/webp": ".webp"}


@router.post("/upload")
def fazer_upload_imagem(
    arquivo: UploadFile = File(...),
    _admin: Usuario = Depends(require_admin),
):
    if arquivo.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato inválido. Envie uma imagem PNG ou WEBP.",
        )

    conteudo = arquivo.file.read(MAX_IMAGE_SIZE + 1)
    if len(conteudo) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="A imagem não pode ultrapassar 5 MB.",
        )

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")
    if not supabase_url or not service_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload não configurado: defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY.",
        )

    object_name = f"products/{uuid4().hex}{ALLOWED_IMAGE_TYPES[arquivo.content_type]}"
    upload_url = (
        f"{supabase_url.rstrip('/')}/storage/v1/object/"
        f"{bucket}/{PurePosixPath(object_name)}"
    )
    try:
        resposta = httpx.put(
            upload_url,
            content=conteudo,
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Content-Type": arquivo.content_type,
                "x-upsert": "false",
            },
            timeout=30,
        )
        resposta.raise_for_status()
    except httpx.HTTPError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível enviar a imagem para o Supabase Storage.",
        ) from erro

    public_url = (
        f"{supabase_url.rstrip('/')}/storage/v1/object/public/"
        f"{bucket}/{object_name}"
    )
    return {
        "url": public_url,
        "imagem_url": public_url,
        "nome": object_name,
        "tipo": arquivo.content_type,
        "tamanho": len(conteudo),
    }


@router.get("/hero-banner", response_model=HeroBannerResponse)
def obter_hero_banner(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    banners = db.query(HeroBanner).order_by(HeroBanner.id).all()
    return {"campanhas": banners}


@router.patch("/hero-banner", response_model=HeroBannerResponse)
def salvar_hero_banner(
    banner_data: AtualizarBanners,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    ids_recebidos = set()
    for campanha_data in banner_data.campanhas:
        frase = campanha_data.frase_promocional.strip()
        if not frase:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A frase promocional não pode ser vazia.",
            )

        if campanha_data.id is None:
            banner = HeroBanner()
            db.add(banner)
        else:
            banner = db.query(HeroBanner).filter(
                HeroBanner.id == campanha_data.id
            ).first()
            if banner is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campanha {campanha_data.id} não encontrada.",
                )
            ids_recebidos.add(campanha_data.id)

        banner.imagem_url = str(campanha_data.imagem_url)
        banner.frase_promocional = frase
        banner.badge = campanha_data.badge
        banner.titulo = campanha_data.titulo
        banner.subtitulo = campanha_data.subtitulo
        banner.link = campanha_data.link
        banner.texto_botao = campanha_data.texto_botao
        if campanha_data.id is None:
            db.flush()
        ids_recebidos.add(banner.id)

    for banner in db.query(HeroBanner).all():
        if banner.id not in ids_recebidos:
            db.delete(banner)

    db.commit()
    banners_salvos = db.query(HeroBanner).order_by(HeroBanner.id).all()
    return {"campanhas": banners_salvos}


@router.post("/users", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_lojista(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    email = str(usuario_data.email).strip().lower()
    usuario_existente = (
        db.query(Usuario).filter(Usuario.email == email).first()
    )
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado no sistema.",
        )

    lojista = Usuario(
        nome=usuario_data.nome,
        email=email,
        hashed_password=hash_password(usuario_data.senha),
        role="admin",
    )
    db.add(lojista)
    db.commit()
    db.refresh(lojista)
    return lojista


@router.get("/catalog/categories")
def listar_categorias(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    return db.query(Categoria).order_by(Categoria.nome).all()


@router.get("/catalog/subcategories")
def listar_subcategorias(
    categoria_id: int | None = None,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    consulta = db.query(Subcategoria)
    if categoria_id is not None:
        consulta = consulta.filter(Subcategoria.categoria_id == categoria_id)
    return consulta.order_by(Subcategoria.nome).all()


@router.get("/catalog/teams")
def listar_times(
    subcategoria_id: int | None = None,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    consulta = db.query(Time)
    if subcategoria_id is not None:
        consulta = consulta.filter(Time.subcategoria_id == subcategoria_id)
    return consulta.order_by(Time.nome).all()


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
