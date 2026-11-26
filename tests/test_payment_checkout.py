import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.pagamentos import _criar_pedido, obter_status_pagamento
from app.db.database import Base
from app.db.models import (
    Produto,
    TamanhoEnum,
    Usuario,
    VariacaoProduto,
)
from app.schemas.pagamento import PagamentoPixCreate


class PaymentCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_order_total_comes_from_database_and_stock_waits_for_approval(self):
        usuario = Usuario(
            nome="Ana Silva",
            email="ana@example.com",
            hashed_password="not-used",
        )
        produto = Produto(
            time_id=1,
            nome="Camisa",
            preco=10.0,
            desconto_percentual=20.0,
            imagem_capa="camisa.png",
            ativo=True,
        )
        variacao = VariacaoProduto(
            tamanho=TamanhoEnum.M,
            estoque=5,
            produto=produto,
        )
        self.session.add_all([usuario, produto, variacao])
        self.session.commit()

        checkout = PagamentoPixCreate(
            itens=[
                {"variacao_id": variacao.id, "quantidade": 1},
                {"variacao_id": variacao.id, "quantidade": 1},
            ],
            cpf="529.982.247-25",
        )
        pedido = _criar_pedido(checkout, "pix", usuario, self.session)

        self.assertEqual(pedido.total, 16.0)
        self.assertEqual(len(pedido.itens), 1)
        self.assertEqual(pedido.itens[0].quantidade, 2)
        self.assertEqual(variacao.estoque, 5)

    def test_approved_status_decrements_stock_only_once(self):
        usuario = Usuario(
            nome="Ana Silva",
            email="ana@example.com",
            hashed_password="not-used",
        )
        outro_usuario = Usuario(
            nome="Bruno",
            email="bruno@example.com",
            hashed_password="not-used",
        )
        produto = Produto(
            time_id=1,
            nome="Camisa",
            preco=10.0,
            desconto_percentual=0.0,
            imagem_capa="camisa.png",
            ativo=True,
        )
        variacao = VariacaoProduto(
            tamanho=TamanhoEnum.M,
            estoque=5,
            produto=produto,
        )
        self.session.add_all([usuario, outro_usuario, produto, variacao])
        self.session.commit()
        checkout = PagamentoPixCreate(
            itens=[{"variacao_id": variacao.id, "quantidade": 2}],
            cpf="52998224725",
        )
        pedido = _criar_pedido(checkout, "pix", usuario, self.session)
        order_id = "ORDTST01M8AQV89XC3XMBZRN8QB33VHN"
        pedido.mp_payment_id = order_id
        self.session.commit()

        with patch(
            "app.api.v1.pagamentos.consultar_pagamento",
            return_value={"status": "approved"},
        ) as consulta:
            with self.assertRaises(HTTPException) as erro:
                obter_status_pagamento(
                    order_id, self.session, outro_usuario
                )
            self.assertEqual(erro.exception.status_code, 404)
            consulta.assert_not_called()

            resultado = obter_status_pagamento(
                order_id, self.session, usuario
            )
            self.assertEqual(resultado.status, "approved")
            self.assertEqual(variacao.estoque, 3)

            consulta.assert_called_once_with(order_id)
            obter_status_pagamento(order_id, self.session, usuario)
            self.assertEqual(variacao.estoque, 3)


if __name__ == "__main__":
    unittest.main()
