"""
Views para cobranças (Billing) AbacatePay
"""

import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from orders.models import Order
from ..models import AbacatePayBilling, AbacatePayCustomer, AbacatePayPayment
from ..serializers import (
    BillingCreateSerializer,
    BillingSerializer,
    BillingStatusSerializer,
)
from ..services import AbacatePayService
from ..docs.billing import (
    billing_create_schema,
    billing_list_schema,
    billing_status_schema,
    billing_pix_qrcode_schema,
    billing_pix_check_schema,
    billing_simulate_schema,
)

logger = logging.getLogger(__name__)


class BillingCreateView(APIView):
    """
    View para criar uma nova cobrança na AbacatePay
    """

    permission_classes = [IsAuthenticated]

    @billing_create_schema
    def post(self, request):
        """Cria uma nova cobrança para um pedido"""
        serializer = BillingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        description = serializer.validated_data.get(
            "description",
            f"Pedido {order_id}",
        )
        metadata = serializer.validated_data.get("metadata", {})

        try:
            order = Order.objects.get(
                order_id=order_id,
                user=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Pedido não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(order, "abacatepay_billing"):
            return Response(
                {
                    "error": "Já existe uma cobrança para este pedido",
                    "billing": BillingSerializer(order.abacatepay_billing).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer, created = AbacatePayCustomer.objects.get_or_create(
            user=request.user,
            defaults={"external_id": ""},
        )

        metadata.update(
            {
                "order_id": order.order_id,
                "user_id": str(request.user.id),
                "user_email": request.user.email or "",
                "user_name": f"{request.user.first_name or ''} {request.user.last_name or ''}".strip()
                or request.user.username
                or "",
            }
        )

        if not customer.external_id:
            import re

            cpf_clean = re.sub(r"\D", "", request.user.cpf or "")
            has_valid_cpf = (
                cpf_clean and cpf_clean != "00000000000" and len(cpf_clean) == 11
            )

            if has_valid_cpf:
                user_name = f"{request.user.first_name or ''} {request.user.last_name or ''}".strip()
                if not user_name:
                    user_name = request.user.username or request.user.email
                    if not user_name:
                        logger.warning(
                            f"Usuário {request.user.id} não possui nome completo, pulando criação de cliente"
                        )
                    else:
                        customer_response = AbacatePayService.create_customer(
                            user_id=str(request.user.id),
                            email=request.user.email,
                            name=user_name,
                            cellphone=request.user.telefone,
                            tax_id=request.user.cpf,
                            metadata={"username": request.user.username or ""},
                        )

                        if not customer_response.get("error") and customer_response.get(
                            "data"
                        ):
                            customer.external_id = customer_response["data"].get(
                                "id", ""
                            )
                            customer.metadata = customer_response["data"].get(
                                "metadata", {}
                            )
                            customer.save()
                else:
                    customer_response = AbacatePayService.create_customer(
                        user_id=str(request.user.id),
                        email=request.user.email,
                        name=user_name,
                        cellphone=request.user.telefone,
                        tax_id=request.user.cpf,
                        metadata={"username": request.user.username or ""},
                    )

                    if not customer_response.get("error") and customer_response.get(
                        "data"
                    ):
                        customer.external_id = customer_response["data"].get("id", "")
                        customer.metadata = customer_response["data"].get(
                            "metadata", {}
                        )
                        customer.save()

        products = []
        for item in order.items.all():
            item_name = "Produto"
            if hasattr(item.item, "name"):
                item_name = item.item.name
            elif hasattr(item.item, "name_pt_br") and item.item.name_pt_br:
                item_name = item.item.name_pt_br

            external_id = f"order_item_{item.id}"

            item_description = ""
            if hasattr(item.item, "description"):
                item_description = item.item.description or ""
            elif (
                hasattr(item.item, "description_pt_br") and item.item.description_pt_br
            ):
                item_description = item.item.description_pt_br

            products.append(
                {
                    "externalId": external_id,
                    "name": item_name,
                    "description": item_description
                    or f"{item_name} - Quantidade: {item.quantity}",
                    "quantity": item.quantity,
                    "price": int(item.unit_price * 100),
                }
            )

        if not products:
            products = [
                {
                    "externalId": f"order_{order.order_id}",
                    "name": description or "Produto",
                    "description": description or "Produto do pedido",
                    "quantity": 1,
                    "price": int(order.total * 100),
                }
            ]

        from django.conf import settings

        origin = request.META.get("HTTP_ORIGIN", "")
        if not origin:
            frontend_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
            if not frontend_origins:
                return Response(
                    {
                        "error": "CORS_ALLOWED_ORIGINS não configurado e Origin header não fornecido",
                        "message": "Configure CORS_ALLOWED_ORIGINS no settings.py ou forneça o Origin header",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            origin = frontend_origins[0]

        from urllib.parse import quote

        encoded_order_id = quote(order.order_id, safe="")
        return_url = f"{origin}/payment?order_id={encoded_order_id}"

        completion_url = f"{origin}/payment/success?order_id={encoded_order_id}"

        billing_response = AbacatePayService.create_billing(
            customer_id=customer.external_id or None,
            amount=order.total,
            description=description,
            products=products,
            return_url=return_url,
            completion_url=completion_url,
            metadata=metadata,
        )

        if billing_response.get("error"):
            error_details = billing_response["error"]

            if (
                isinstance(error_details, dict)
                and error_details.get("statusCode") == 401
            ):
                return Response(
                    {
                        "error": "API key não configurada",
                        "message": error_details.get(
                            "message", "ABACATEPAY_API_KEY não está configurada"
                        ),
                        "details": "Configure a variável de ambiente ABACATEPAY_API_KEY no arquivo .env",
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Trata erros de timeout e serviço indisponível (522, 524, 503, 504)
            if isinstance(error_details, dict):
                status_code = error_details.get("statusCode")
                error_type = error_details.get("type")

                if status_code in (522, 524, 503, 504) or error_type in (
                    "timeout",
                    "connection_error",
                    "service_unavailable",
                ):
                    return Response(
                        {
                            "error": "Serviço de pagamento indisponível",
                            "message": error_details.get(
                                "message",
                                "O serviço de pagamento está temporariamente indisponível. Por favor, tente novamente em alguns instantes.",
                            ),
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )

            if (
                isinstance(error_details, dict)
                and error_details.get("statusCode") == 404
            ):
                docs_url = getattr(
                    settings, "ABACATEPAY_DOCS_URL", "https://docs.abacatepay.com"
                )
                return Response(
                    {
                        "error": "Endpoint da API AbacatePay não encontrado",
                        "details": error_details,
                        "message": f"Por favor, verifique a documentação da API em {docs_url} para confirmar os endpoints corretos e a configuração da API_KEY",
                        "tried_endpoints": [
                            "/v1/billing/create",
                        ],
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Retorna mensagem amigável do erro se disponível
            error_message = "Erro ao criar cobrança na AbacatePay"
            if isinstance(error_details, dict) and error_details.get("message"):
                error_message = error_details.get("message")

            return Response(
                {
                    "error": "Erro ao criar cobrança na AbacatePay",
                    "message": error_message,
                    "details": error_details,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        billing_data = billing_response["data"]

        if not customer.external_id and billing_data.get("customerId"):
            customer.external_id = billing_data["customerId"]
            customer.save()

        billing = AbacatePayBilling.objects.create(
            order=order,
            customer=customer,
            billing_id=billing_data["id"],
            payment_url=billing_data.get("url", ""),
            amount=order.total,
            status=billing_data.get("status", "PENDING"),
            methods=billing_data.get("methods", []),
            frequency=billing_data.get("frequency", "ONE_TIME"),
            dev_mode=billing_data.get("devMode", False),
        )

        AbacatePayPayment.objects.create(
            billing=billing,
            order=order,
            payment_url=billing.payment_url,
            amount=order.total,
            status=billing.status,
            raw_response=billing_data,
        )

        return Response(
            BillingSerializer(billing).data,
            status=status.HTTP_201_CREATED,
        )


class BillingListView(APIView):
    """
    View para listar cobranças do usuário
    """

    permission_classes = [IsAuthenticated]

    @billing_list_schema
    def get(self, request):
        """Lista todas as cobranças do usuário autenticado"""
        billings = (
            AbacatePayBilling.objects.filter(
                customer__user=request.user,
            )
            .select_related("order", "customer")
            .order_by("-created_at")
        )

        serializer = BillingSerializer(billings, many=True)
        return Response(serializer.data)


class BillingStatusView(APIView):
    """
    View para verificar status de uma cobrança
    """

    permission_classes = [IsAuthenticated]

    @billing_status_schema
    def get(self, request, billing_id):
        """Verifica o status de uma cobrança"""
        try:
            billing = AbacatePayBilling.objects.get(
                billing_id=billing_id,
                customer__user=request.user,
            )
        except AbacatePayBilling.DoesNotExist:
            return Response(
                {"error": "Cobrança não encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        status_response = AbacatePayService.get_billing_status(billing_id)

        if status_response.get("error"):
            return Response(
                BillingStatusSerializer(
                    {
                        "billing_id": billing.billing_id,
                        "status": billing.status,
                        "amount": billing.amount,
                        "payment_url": billing.payment_url,
                        "methods": billing.methods,
                    }
                ).data
            )

        status_data = status_response["data"]
        billing.status = status_data.get("status", billing.status)
        billing.payment_url = status_data.get("url", billing.payment_url)
        billing.methods = status_data.get("methods", billing.methods)
        billing.save()

        if billing.status == "PAID" and billing.order.status != "paid":
            billing.order.status = "paid"
            billing.order.paid_at = timezone.now()
            billing.order.save()

        return Response(
            BillingStatusSerializer(
                {
                    "billing_id": billing.billing_id,
                    "status": billing.status,
                    "amount": billing.amount,
                    "payment_url": billing.payment_url,
                    "methods": billing.methods,
                }
            ).data
        )


class BillingPixQRCodeView(APIView):
    """
    View para criar QRCode PIX de uma cobrança
    """

    permission_classes = [IsAuthenticated]

    @billing_pix_qrcode_schema
    def post(self, request, billing_id):
        """Cria QRCode PIX para uma cobrança"""
        exists = AbacatePayBilling.objects.filter(
            billing_id=billing_id, customer__user=request.user
        ).exists()
        if not exists:
            return Response(
                {"error": "Cobrança não encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        qrcode_response = AbacatePayService.create_pix_qrcode(billing_id)

        if qrcode_response.get("error"):
            return Response(
                {
                    "error": "Erro ao criar QRCode PIX",
                    "details": qrcode_response["error"],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(qrcode_response["data"])


class BillingPixCheckView(APIView):
    """
    View para verificar status de pagamento PIX
    """

    permission_classes = [IsAuthenticated]

    @billing_pix_check_schema
    def get(self, request, billing_id):
        """Verifica status de pagamento PIX"""
        try:
            billing = AbacatePayBilling.objects.get(
                billing_id=billing_id,
                customer__user=request.user,
            )
        except AbacatePayBilling.DoesNotExist:
            return Response(
                {"error": "Cobrança não encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        check_response = AbacatePayService.check_pix_status(billing_id)

        if check_response.get("error"):
            return Response(
                {
                    "error": "Erro ao verificar status PIX",
                    "details": check_response["error"],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        status_data = check_response.get("data", {})
        if status_data.get("status") == "PAID" and billing.status != "PAID":
            billing.status = "PAID"
            billing.save()

            if billing.order.status != "paid":
                billing.order.status = "paid"
                billing.order.paid_at = timezone.now()
                billing.order.save()

        return Response(check_response["data"])


class BillingSimulateView(APIView):
    """
    View para simular pagamento (apenas em dev mode)
    """

    permission_classes = [IsAuthenticated]

    @billing_simulate_schema
    def post(self, request, billing_id):
        """Simula um pagamento (apenas em modo de desenvolvimento)"""
        try:
            billing = AbacatePayBilling.objects.get(
                billing_id=billing_id,
                customer__user=request.user,
            )
        except AbacatePayBilling.DoesNotExist:
            return Response(
                {"error": "Cobrança não encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not billing.dev_mode:
            return Response(
                {
                    "error": "Simulação de pagamento só está disponível em modo de desenvolvimento"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        simulate_response = AbacatePayService.simulate_payment(billing_id)

        if simulate_response.get("error"):
            return Response(
                {
                    "error": "Erro ao simular pagamento",
                    "details": simulate_response["error"],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        billing.status = "PAID"
        billing.save()

        if billing.order.status != "paid":
            billing.order.status = "paid"
            billing.order.paid_at = timezone.now()
            billing.order.save()

        return Response(simulate_response["data"])
