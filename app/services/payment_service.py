import os
from uuid import uuid4
from typing import Any, Dict

import requests


_ORDERS_URL = "https://api.mercadopago.com/v1/orders"
_REQUEST_TIMEOUT = 30


class MercadoPagoConfigurationError(Exception):
    pass


class MercadoPagoAPIError(Exception):
    pass


def _access_token() -> str:
    access_token = os.getenv("MP_ACCESS_TOKEN")
    if not access_token:
        raise MercadoPagoConfigurationError(
            "Configure MP_ACCESS_TOKEN para habilitar pagamentos."
        )
    access_token = access_token.strip()
    ambiente = os.getenv("MP_ENVIRONMENT", "test").strip().lower()
    if ambiente not in {"test", "production"}:
        raise MercadoPagoConfigurationError(
            "MP_ENVIRONMENT deve ser 'test' ou 'production'."
        )
    if ambiente == "test" and not access_token.startswith(("TEST-", "APP_USR-")):
        raise MercadoPagoConfigurationError(
            "MP_ENVIRONMENT=test exige um Access Token de teste (prefixo TEST- ou APP_USR-)."
        )
    if ambiente == "production" and not access_token.startswith("APP_USR-"):
        raise MercadoPagoConfigurationError(
            "MP_ENVIRONMENT=production exige o Access Token de produção."
        )
    return access_token


def validar_configuracao_mp() -> None:
    _access_token()


def _mensagem_erro_provedor(codigo_http: Any, resposta: Any) -> str:
    detalhes = []
    if isinstance(resposta, dict):
        for campo in ("error", "message"):
            valor = resposta.get(campo)
            if isinstance(valor, str) and valor.strip():
                detalhes.append(" ".join(valor.split())[:200])

        causas = resposta.get("cause")
        if not isinstance(causas, list):
            causas = resposta.get("errors")
        if isinstance(causas, list):
            for causa in causas[:5]:
                if not isinstance(causa, dict):
                    continue
                codigo = causa.get("code")
                descricao = causa.get("description") or causa.get("message")
                texto = " ".join(str(descricao).split())[:200] if descricao else ""
                if isinstance(codigo, (int, str)):
                    texto = f"{codigo}: {texto}" if texto else str(codigo)
                if texto:
                    detalhes.append(texto)

    mensagem = f"Mercado Pago respondeu HTTP {codigo_http}."
    if detalhes:
        mensagem = f"{mensagem} {'; '.join(detalhes)}"
    return mensagem


def _normalizar_order(order: Dict[str, Any]) -> Dict[str, Any]:
    status_order = order.get("status")
    if status_order == "processed":
        order["status"] = "approved"
    elif isinstance(status_order, str) and status_order in {
        "failed",
        "cancelled",
        "expired",
    }:
        order["status"] = "rejected"
    elif status_order == "processing":
        order["status"] = "in_process"
    elif status_order == "created":
        order["status"] = "pending"
    elif not status_order:
        order["status"] = "pending"

    transactions = order.get("transactions")
    payments = transactions.get("payments") if isinstance(transactions, dict) else None
    if isinstance(payments, list) and payments and isinstance(payments[0], dict):
        payment_method = payments[0].get("payment_method")
        if isinstance(payment_method, dict):
            qr_code = payment_method.get("qr_code")
            qr_code_base64 = payment_method.get("qr_code_base64")
            if qr_code or qr_code_base64:
                order["point_of_interaction"] = {
                    "transaction_data": {
                        "qr_code": qr_code,
                        "qr_code_base64": qr_code_base64,
                    }
                }
    return order


def _extrair_order(
    resposta: requests.Response,
    aceitar_pagamento_recusado: bool = False,
) -> Dict[str, Any]:
    try:
        order = resposta.json()
    except ValueError:
        order = None

    order_recusada = (
        aceitar_pagamento_recusado
        and resposta.status_code == 402
        and isinstance(order, dict)
        and bool(order.get("id"))
    )
    if (
        resposta.status_code not in (200, 201)
        and not order_recusada
    ) or not isinstance(order, dict):
        raise MercadoPagoAPIError(
            _mensagem_erro_provedor(resposta.status_code, order)
        )
    if order_recusada and not order.get("status"):
        order["status"] = "failed"
    return _normalizar_order(order)


def _criar_order(dados: Dict[str, Any]) -> Dict[str, Any]:
    access_token = _access_token()
    try:
        resposta = requests.post(
            _ORDERS_URL,
            json=dados,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid4()),
            },
            timeout=_REQUEST_TIMEOUT,
        )
    except requests.RequestException as erro:
        raise MercadoPagoAPIError(
            "Não foi possível conectar ao Mercado Pago."
        ) from erro
    return _extrair_order(resposta, aceitar_pagamento_recusado=True)


def criar_pagamento_pix(
    valor_total: float,
    descricao: str,
    email: str,
    nome: str,
    cpf: str,
    pedido_id: int,
) -> Dict[str, Any]:
    partes_nome = nome.strip().split()
    valor = f"{valor_total:.2f}"
    dados = {
        "type": "online",
        "processing_mode": "automatic",
        "total_amount": valor,
        "description": descricao,
        "external_reference": str(pedido_id),
        "payer": {
            "email": email,
            "first_name": partes_nome[0] if partes_nome else "Cliente",
            "last_name": " ".join(partes_nome[1:]) if len(partes_nome) > 1 else "Cliente",
            "identification": {"type": "CPF", "number": cpf},
        },
        "transactions": {
            "payments": [
                {
                    "amount": valor,
                    "payment_method": {
                        "id": "pix",
                        "type": "bank_transfer",
                    },
                }
            ]
        },
    }
    return _criar_order(dados)


def criar_pagamento_cartao(
    valor_total: float,
    descricao: str,
    email: str,
    nome: str,
    cpf: str,
    token: str,
    installments: int,
    payment_method_id: str,
    pedido_id: int,
) -> Dict[str, Any]:
    partes_nome = nome.strip().split()
    payer = {
        "email": email,
        "first_name": partes_nome[0] if partes_nome else "Cliente",
        "last_name": " ".join(partes_nome[1:]) if len(partes_nome) > 1 else "Cliente",
        "identification": {"type": "CPF", "number": cpf},
    }
    valor = f"{valor_total:.2f}"
    payment_method = {
        "id": payment_method_id,
        "type": "credit_card",
        "token": token,
        "installments": installments,
    }
    dados = {
        "type": "online",
        "processing_mode": "automatic",
        "total_amount": valor,
        "description": descricao,
        "external_reference": str(pedido_id),
        "payer": payer,
        "transactions": {
            "payments": [
                {
                    "amount": valor,
                    "payment_method": payment_method,
                }
            ]
        },
    }
    return _criar_order(dados)


def consultar_pagamento(payment_id: str) -> Dict[str, Any]:
    access_token = _access_token()
    try:
        resposta = requests.get(
            f"{_ORDERS_URL}/{payment_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_REQUEST_TIMEOUT,
        )
    except requests.RequestException as erro:
        raise MercadoPagoAPIError(
            "Não foi possível consultar o pagamento no Mercado Pago."
        ) from erro
    return _extrair_order(resposta)
