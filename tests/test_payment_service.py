import os
import unittest
import uuid
from unittest.mock import Mock, patch

import requests

from app.services.payment_service import (
    MercadoPagoAPIError,
    MercadoPagoConfigurationError,
    consultar_pagamento,
    criar_pagamento_cartao,
    criar_pagamento_pix,
    validar_configuracao_mp,
)


class PaymentServiceTests(unittest.TestCase):
    def _response(self, payload, status_code=201):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = payload
        return response

    def test_pix_posts_order_with_auth_idempotency_and_qr_code(self):
        response = self._response(
            {
                "id": "ORD-123",
                "status": "created",
                "status_detail": "created",
                "transactions": {
                    "payments": [
                        {
                            "payment_method": {
                                "id": "pix",
                                "type": "bank_transfer",
                                "qr_code": "pix-copy-paste",
                                "qr_code_base64": "encoded-qr",
                            }
                        }
                    ]
                },
            }
        )
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "APP_USR-test-token"},
        ):
            with patch(
                "app.services.payment_service.requests.post",
                return_value=response,
            ) as post:
                order = criar_pagamento_pix(
                    25.5,
                    "Pedido 7",
                    "cliente@example.com",
                    "Ana Silva",
                    "52998224725",
                    7,
                )

        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.mercadopago.com/v1/orders")
        self.assertEqual(
            kwargs["headers"]["Authorization"],
            "Bearer APP_USR-test-token",
        )
        idempotency_key = kwargs["headers"]["X-Idempotency-Key"]
        self.assertEqual(uuid.UUID(idempotency_key).version, 4)
        self.assertEqual(kwargs["json"]["type"], "online")
        self.assertEqual(kwargs["json"]["processing_mode"], "automatic")
        self.assertEqual(kwargs["json"]["total_amount"], "25.50")
        self.assertEqual(kwargs["json"]["external_reference"], "7")
        payment = kwargs["json"]["transactions"]["payments"][0]
        self.assertEqual(payment["amount"], "25.50")
        self.assertEqual(payment["payment_method"]["id"], "pix")
        self.assertEqual(payment["payment_method"]["type"], "bank_transfer")
        self.assertEqual(order["id"], "ORD-123")
        self.assertEqual(order["status"], "pending")
        self.assertEqual(
            order["point_of_interaction"]["transaction_data"],
            {
                "qr_code": "pix-copy-paste",
                "qr_code_base64": "encoded-qr",
            },
        )

    def test_card_sends_payment_method_inside_order_transaction(self):
        response = self._response(
            {
                "id": "ORD-456",
                "status": "processed",
                "status_detail": "accredited",
                "transactions": {"payments": []},
            }
        )
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "TEST-token"},
        ):
            with patch(
                "app.services.payment_service.requests.post",
                return_value=response,
            ) as post:
                order = criar_pagamento_cartao(
                    25.5,
                    "Pedido 8",
                    "cliente@example.com",
                    "Ana Silva",
                    "52998224725",
                    "tokenizado-no-frontend",
                    3,
                    "visa",
                    8,
                )

        dados = post.call_args.kwargs["json"]
        payment_method = dados["transactions"]["payments"][0]["payment_method"]
        self.assertEqual(dados["total_amount"], "25.50")
        self.assertEqual(payment_method["id"], "visa")
        self.assertEqual(payment_method["type"], "credit_card")
        self.assertEqual(payment_method["token"], "tokenizado-no-frontend")
        self.assertEqual(payment_method["installments"], 3)
        self.assertNotIn("issuer_id", payment_method)
        self.assertNotIn("card_number", dados)
        self.assertEqual(order["status"], "approved")

    def test_http_402_with_order_is_returned_as_rejected_payment(self):
        response = self._response(
            {
                "id": "ORD-789",
                "status_detail": "cc_rejected_other_reason",
            },
            status_code=402,
        )
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "TEST-token"},
        ):
            with patch(
                "app.services.payment_service.requests.post",
                return_value=response,
            ):
                order = criar_pagamento_pix(
                    25.5,
                    "Pedido 9",
                    "cliente@example.com",
                    "Ana Silva",
                    "52998224725",
                    9,
                )

        self.assertEqual(order["id"], "ORD-789")
        self.assertEqual(order["status"], "rejected")

    def test_non_success_response_without_order_raises_api_error(self):
        response = self._response(
            {
                "error": "bad_request",
                "message": "Invalid payer",
                "cause": [{"code": 1234, "description": "Payer details are invalid"}],
                "debug": "sensitive-value-must-not-be-returned",
            },
            status_code=400,
        )
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "TEST-token"},
        ):
            with patch(
                "app.services.payment_service.requests.post",
                return_value=response,
            ):
                with self.assertRaises(MercadoPagoAPIError) as erro:
                    criar_pagamento_pix(
                        25.5,
                        "Pedido 10",
                        "cliente@example.com",
                        "Ana Silva",
                        "52998224725",
                        10,
                    )

        self.assertIn("HTTP 400", str(erro.exception))
        self.assertIn("bad_request", str(erro.exception))
        self.assertIn("1234: Payer details are invalid", str(erro.exception))
        self.assertNotIn("sensitive-value-must-not-be-returned", str(erro.exception))

    def test_order_status_uses_get_orders_endpoint(self):
        response = self._response(
            {
                "id": "ORD-123",
                "status": "processed",
                "status_detail": "accredited",
            },
            status_code=200,
        )
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "TEST-token"},
        ):
            with patch(
                "app.services.payment_service.requests.get",
                return_value=response,
            ) as get:
                order = consultar_pagamento("ORD-123")

        args, kwargs = get.call_args
        self.assertEqual(
            args[0],
            "https://api.mercadopago.com/v1/orders/ORD-123",
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer TEST-token")
        self.assertEqual(order["status"], "approved")

    def test_network_error_raises_api_error(self):
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "TEST-token"},
        ):
            with patch(
                "app.services.payment_service.requests.post",
                side_effect=requests.ConnectionError,
            ):
                with self.assertRaisesRegex(
                    MercadoPagoAPIError,
                    "Não foi possível conectar",
                ):
                    criar_pagamento_pix(
                        25.5,
                        "Pedido 11",
                        "cliente@example.com",
                        "Ana Silva",
                        "52998224725",
                        11,
                    )

    def test_test_environment_rejects_unknown_access_token_prefix(self):
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "test", "MP_ACCESS_TOKEN": "LIVE-token"},
        ):
            with self.assertRaisesRegex(
                MercadoPagoConfigurationError,
                "Access Token de teste",
            ):
                validar_configuracao_mp()

    def test_test_environment_accepts_app_usr_access_token(self):
        with patch.dict(
            os.environ,
            {
                "MP_ENVIRONMENT": "test",
                "MP_ACCESS_TOKEN": "APP_USR-test-token",
            },
        ):
            validar_configuracao_mp()

    def test_production_environment_rejects_test_access_token(self):
        with patch.dict(
            os.environ,
            {"MP_ENVIRONMENT": "production", "MP_ACCESS_TOKEN": "TEST-token"},
        ):
            with self.assertRaisesRegex(
                MercadoPagoConfigurationError,
                "Access Token de produção",
            ):
                validar_configuracao_mp()


if __name__ == "__main__":
    unittest.main()
