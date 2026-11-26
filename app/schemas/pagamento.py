import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ItemPedidoCreate(BaseModel):
    variacao_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class CheckoutBase(BaseModel):
    itens: List[ItemPedidoCreate] = Field(min_length=1)
    cpf: str

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        cpf = re.sub(r"\D", "", valor)
        if len(cpf) != 11 or len(set(cpf)) == 1:
            raise ValueError("Informe um CPF válido.")

        digitos = [int(digito) for digito in cpf]
        for tamanho in (9, 10):
            soma = sum(
                digitos[indice] * (tamanho + 1 - indice)
                for indice in range(tamanho)
            )
            digito = (soma * 10) % 11
            digito = 0 if digito == 10 else digito
            if digito != digitos[tamanho]:
                raise ValueError("Informe um CPF válido.")

        return cpf


class PagamentoPixCreate(CheckoutBase):
    pass


class PagamentoCartaoCreate(CheckoutBase):
    token: str = Field(min_length=1)
    installments: int = Field(ge=1)
    payment_method_id: str = Field(min_length=1)


class PagamentoResponse(BaseModel):
    pedido_id: int
    payment_id: str
    status: str
    status_detail: Optional[str] = None
    pix_qr_code: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None


class StatusPagamentoResponse(BaseModel):
    pedido_id: int
    payment_id: str
    status: str
    status_detail: Optional[str] = None
