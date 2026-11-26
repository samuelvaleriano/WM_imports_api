from collections import defaultdict
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import ItemPedido, Pedido, Produto, Usuario, VariacaoProduto
from app.schemas.pagamento import (
    PagamentoCartaoCreate,
    PagamentoPixCreate,
    PagamentoResponse,
    StatusPagamentoResponse,
)
from app.services.payment_service import (
    MercadoPagoAPIError,
    MercadoPagoConfigurationError,
    consultar_pagamento,
    criar_pagamento_cartao,
    criar_pagamento_pix,
    validar_configuracao_mp,
)

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


def _criar_pedido(
    dados_checkout: PagamentoPixCreate | PagamentoCartaoCreate,
    metodo_pagamento: str,
    usuario: Usuario,
    db: Session,
) -> Pedido:
    quantidades: Dict[int, int] = defaultdict(int)
    for item in dados_checkout.itens:
        quantidades[item.variacao_id] += item.quantidade

    variacoes: Dict[int, Tuple[VariacaoProduto, Produto, int, float]] = {}
    total = 0.0
    for variacao_id, quantidade in quantidades.items():
        variacao = (
            db.query(VariacaoProduto)
            .filter(VariacaoProduto.id == variacao_id)
            .with_for_update()
            .first()
        )
        if variacao is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variação {variacao_id} não encontrada.",
            )
        produto = db.query(Produto).filter(Produto.id == variacao.produto_id).first()
        if produto is None or not produto.ativo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O produto da variação {variacao_id} não está disponível.",
            )
        if produto.preco <= 0 or produto.desconto_percentual < 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O preço de {produto.nome} não está configurado corretamente.",
            )
        if (variacao.estoque or 0) < quantidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Estoque insuficiente para {produto.nome} ({variacao.tamanho.value}).",
            )

        preco = round(produto.preco * (1 - produto.desconto_percentual / 100), 2)
        total += preco * quantidade
        variacoes[variacao_id] = (variacao, produto, quantidade, preco)

    total = round(total, 2)
    if total <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O valor do pedido deve ser maior que zero.",
        )

    pedido = Pedido(
        usuario_id=usuario.id,
        total=total,
        metodo_pagamento=metodo_pagamento,
        status_pagamento="pending",
    )
    db.add(pedido)
    db.flush()
    for variacao, produto, quantidade, preco in variacoes.values():
        pedido.itens.append(
            ItemPedido(
                variacao_id=variacao.id,
                produto_id=produto.id,
                produto_nome=produto.nome,
                tamanho=variacao.tamanho.value,
                quantidade=quantidade,
                preco_unitario=preco,
            )
        )
    db.commit()
    db.refresh(pedido)
    return pedido


def _registrar_falha_pagamento(pedido: Pedido, db: Session) -> None:
    pedido.status_pagamento = "failed"
    db.commit()


def _baixar_estoque(pedido: Pedido, db: Session) -> None:
    if pedido.estoque_baixado:
        return
    for item in pedido.itens:
        variacao = (
            db.query(VariacaoProduto)
            .filter(VariacaoProduto.id == item.variacao_id)
            .with_for_update()
            .first()
        )
        if variacao is not None:
            variacao.estoque = (variacao.estoque or 0) - item.quantidade
    pedido.estoque_baixado = True


def _nome_pagador(usuario: Usuario) -> str:
    return usuario.nome or "Cliente"


@router.post(
    "/pix",
    response_model=PagamentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def pagar_com_pix(
    checkout: PagamentoPixCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> PagamentoResponse:
    try:
        validar_configuracao_mp()
    except MercadoPagoConfigurationError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(erro),
        ) from erro
    pedido = _criar_pedido(checkout, "pix", usuario, db)
    try:
        pagamento = criar_pagamento_pix(
            valor_total=pedido.total,
            descricao=f"WM Imports - Pedido {pedido.id}",
            email=usuario.email,
            nome=_nome_pagador(usuario),
            cpf=checkout.cpf,
            pedido_id=pedido.id,
        )
    except MercadoPagoConfigurationError as erro:
        _registrar_falha_pagamento(pedido, db)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(erro),
        ) from erro
    except MercadoPagoAPIError as erro:
        _registrar_falha_pagamento(pedido, db)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(erro),
        ) from erro

    payment_id = pagamento.get("id")
    interacao = pagamento.get("point_of_interaction") or {}
    dados_transacao = interacao.get("transaction_data") or {}
    if not payment_id:
        _registrar_falha_pagamento(pedido, db)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O Mercado Pago não retornou o identificador do pagamento.",
        )

    pedido.mp_payment_id = str(payment_id)
    pedido.status_pagamento = str(pagamento.get("status", "pending"))
    pedido.pix_qr_code = dados_transacao.get("qr_code")
    pedido.pix_qr_code_base64 = dados_transacao.get("qr_code_base64")
    if pedido.status_pagamento == "approved":
        _baixar_estoque(pedido, db)
    db.commit()
    return PagamentoResponse(
        pedido_id=pedido.id,
        payment_id=pedido.mp_payment_id,
        status=pedido.status_pagamento,
        status_detail=pagamento.get("status_detail"),
        pix_qr_code=pedido.pix_qr_code,
        pix_qr_code_base64=pedido.pix_qr_code_base64,
    )


@router.post(
    "/cartao",
    response_model=PagamentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def pagar_com_cartao(
    checkout: PagamentoCartaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> PagamentoResponse:
    try:
        validar_configuracao_mp()
    except MercadoPagoConfigurationError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(erro),
        ) from erro
    pedido = _criar_pedido(checkout, "credit_card", usuario, db)
    try:
        pagamento = criar_pagamento_cartao(
            valor_total=pedido.total,
            descricao=f"WM Imports - Pedido {pedido.id}",
            email=usuario.email,
            nome=_nome_pagador(usuario),
            cpf=checkout.cpf,
            token=checkout.token,
            installments=checkout.installments,
            payment_method_id=checkout.payment_method_id,
            pedido_id=pedido.id,
        )
    except MercadoPagoConfigurationError as erro:
        _registrar_falha_pagamento(pedido, db)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(erro),
        ) from erro
    except MercadoPagoAPIError as erro:
        _registrar_falha_pagamento(pedido, db)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(erro),
        ) from erro

    payment_id = pagamento.get("id")
    if not payment_id:
        _registrar_falha_pagamento(pedido, db)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O Mercado Pago não retornou o identificador do pagamento.",
        )

    pedido.mp_payment_id = str(payment_id)
    pedido.status_pagamento = str(pagamento.get("status", "pending"))
    if pedido.status_pagamento == "approved":
        _baixar_estoque(pedido, db)
    db.commit()
    return PagamentoResponse(
        pedido_id=pedido.id,
        payment_id=pedido.mp_payment_id,
        status=pedido.status_pagamento,
        status_detail=pagamento.get("status_detail"),
    )


@router.get(
    "/{payment_id}/status",
    response_model=StatusPagamentoResponse,
)
def obter_status_pagamento(
    payment_id: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> StatusPagamentoResponse:
    pedido = (
        db.query(Pedido)
        .filter(
            Pedido.mp_payment_id == payment_id,
            Pedido.usuario_id == usuario.id,
        )
        .with_for_update()
        .first()
    )
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Pagamento não encontrado para o usuário autenticado. "
                "Consulte o pagamento na mesma conta que iniciou o pedido."
            ),
        )

    try:
        pagamento = consultar_pagamento(payment_id)
    except MercadoPagoConfigurationError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(erro),
        ) from erro
    except MercadoPagoAPIError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(erro),
        ) from erro

    status_pagamento = pagamento.get("status")
    if not status_pagamento:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O Mercado Pago não retornou o status do pagamento.",
        )

    pedido.status_pagamento = str(status_pagamento)
    if status_pagamento == "approved" and not pedido.estoque_baixado:
        _baixar_estoque(pedido, db)
    db.commit()
    return StatusPagamentoResponse(
        pedido_id=pedido.id,
        payment_id=payment_id,
        status=pedido.status_pagamento,
        status_detail=pagamento.get("status_detail"),
    )
