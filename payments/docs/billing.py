"""
Documentação das rotas de cobranças (Billing) AbacatePay.
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from ..serializers.billing import (
    BillingCreateSerializer,
    BillingSerializer,
    BillingStatusSerializer,
)


billing_create_schema = extend_schema(
    operation_id="billing_create",
    tags=["payments"],
    summary="Criar uma nova cobrança AbacatePay",
    description="""
    Cria uma nova cobrança na AbacatePay para um pedido existente.
    
    **Processo:**
    1. Verifica se o pedido existe e pertence ao usuário
    2. Cria ou busca o cliente na AbacatePay
    3. Cria a cobrança na API da AbacatePay
    4. Salva os dados no banco de dados
    5. Retorna a URL de pagamento
    
    **Métodos de pagamento disponíveis:**
    - PIX
    - Cartão de Crédito
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    request=BillingCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=BillingSerializer,
            description="Cobrança criada com sucesso",
            examples=[
                OpenApiExample(
                    name="Cobrança criada",
                    value={
                        "id": 1,
                        "billing_id": "bill_12345667",
                        "order": 1,
                        "order_id": "#KFNSFG",
                        "customer": 1,
                        "customer_external_id": "cust_12345",
                        "payment_url": "https://abacatepay.com/pay/bill_12345667",
                        "amount": "100.00",
                        "status": "PENDING",
                        "methods": ["PIX", "CARD"],
                        "frequency": "ONE_TIME",
                        "dev_mode": True,
                        "created_at": "2024-01-20T14:30:00Z",
                        "updated_at": "2024-01-20T14:30:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Dados inválidos ou cobrança já existe",
            examples=[
                OpenApiExample(
                    name="Cobrança já existe",
                    value={
                        "error": "Já existe uma cobrança para este pedido",
                        "billing": {
                            "billing_id": "bill_12345667",
                            "payment_url": "https://abacatepay.com/pay/bill_12345667",
                        },
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description="Pedido não encontrado",
            examples=[
                OpenApiExample(
                    name="Pedido não encontrado",
                    value={
                        "error": "Pedido não encontrado",
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="Erro ao criar cobrança na AbacatePay",
            examples=[
                OpenApiExample(
                    name="Erro na API",
                    value={
                        "error": "Erro ao criar cobrança na AbacatePay",
                        "details": {"message": "Invalid API key"},
                    },
                ),
            ],
        ),
    },
)


billing_list_schema = extend_schema(
    operation_id="billing_list",
    tags=["payments"],
    summary="Listar cobranças do usuário",
    description="""
    Lista todas as cobranças do usuário autenticado, ordenadas pelas mais recentes primeiro.
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    responses={
        200: OpenApiResponse(
            response=BillingSerializer(many=True),
            description="Lista de cobranças retornada com sucesso",
            examples=[
                OpenApiExample(
                    name="Lista de cobranças",
                    value=[
                        {
                            "id": 1,
                            "billing_id": "bill_12345667",
                            "order_id": "#KFNSFG",
                            "payment_url": "https://abacatepay.com/pay/bill_12345667",
                            "amount": "100.00",
                            "status": "PAID",
                            "methods": ["PIX"],
                            "created_at": "2024-01-20T14:30:00Z",
                        },
                        {
                            "id": 2,
                            "billing_id": "bill_12345668",
                            "order_id": "#KFNSGH",
                            "payment_url": "https://abacatepay.com/pay/bill_12345668",
                            "amount": "50.00",
                            "status": "PENDING",
                            "methods": ["PIX", "CARD"],
                            "created_at": "2024-01-20T15:00:00Z",
                        },
                    ],
                    response_only=True,
                ),
            ],
        ),
    },
)


billing_status_schema = extend_schema(
    operation_id="billing_status",
    tags=["payments"],
    summary="Verificar status de uma cobrança",
    description="""
    Verifica o status atualizado de uma cobrança na AbacatePay.
    
    **Status possíveis:**
    - `PENDING`: Cobrança pendente de pagamento
    - `PAID`: Cobrança paga
    - `EXPIRED`: Cobrança expirada
    - `CANCELLED`: Cobrança cancelada
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    parameters=[
        OpenApiParameter(
            name="billing_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="ID da cobrança na AbacatePay (ex: bill_12345667)",
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=BillingStatusSerializer,
            description="Status da cobrança retornado com sucesso",
            examples=[
                OpenApiExample(
                    name="Cobrança pendente",
                    value={
                        "billing_id": "bill_12345667",
                        "status": "PENDING",
                        "amount": "100.00",
                        "payment_url": "https://abacatepay.com/pay/bill_12345667",
                        "methods": ["PIX", "CARD"],
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    name="Cobrança paga",
                    value={
                        "billing_id": "bill_12345667",
                        "status": "PAID",
                        "amount": "100.00",
                        "payment_url": "https://abacatepay.com/pay/bill_12345667",
                        "methods": ["PIX"],
                    },
                    response_only=True,
                ),
            ],
        ),
        404: OpenApiResponse(
            description="Cobrança não encontrada",
            examples=[
                OpenApiExample(
                    name="Não encontrada",
                    value={
                        "error": "Cobrança não encontrada",
                    },
                ),
            ],
        ),
    },
)


billing_pix_qrcode_schema = extend_schema(
    operation_id="billing_pix_qrcode",
    tags=["payments"],
    summary="Criar QRCode PIX para uma cobrança",
    description="""
    Cria um QRCode PIX para uma cobrança específica.
    
    **Uso:**
    - Use esta rota quando quiser gerar um QRCode PIX para pagamento
    - O QRCode pode ser escaneado por qualquer app de pagamento PIX
    - O pagamento será confirmado automaticamente via webhook
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    parameters=[
        OpenApiParameter(
            name="billing_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="ID da cobrança na AbacatePay",
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="QRCode PIX criado com sucesso",
            examples=[
                OpenApiExample(
                    name="QRCode criado",
                    value={
                        "qrcode": "00020126580014br.gov.bcb.pix...",
                        "qrcode_image": "https://api.abacatepay.com/qrcode/bill_12345667.png",
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description="Cobrança não encontrada",
        ),
        500: OpenApiResponse(
            description="Erro ao criar QRCode PIX",
        ),
    },
)


billing_pix_check_schema = extend_schema(
    operation_id="billing_pix_check",
    tags=["payments"],
    summary="Verificar status de pagamento PIX",
    description="""
    Verifica o status de pagamento PIX de uma cobrança.
    
    **Uso:**
    - Use esta rota para verificar se o pagamento PIX foi confirmado
    - Recomenda-se usar webhooks para atualizações em tempo real
    - Esta rota é útil para polling manual
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    parameters=[
        OpenApiParameter(
            name="billing_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="ID da cobrança na AbacatePay",
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Status do pagamento PIX",
            examples=[
                OpenApiExample(
                    name="Pagamento pendente",
                    value={
                        "status": "PENDING",
                        "billing_id": "bill_12345667",
                    },
                ),
                OpenApiExample(
                    name="Pagamento confirmado",
                    value={
                        "status": "PAID",
                        "billing_id": "bill_12345667",
                        "paid_at": "2024-01-20T14:35:00Z",
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description="Cobrança não encontrada",
        ),
    },
)


billing_simulate_schema = extend_schema(
    operation_id="billing_simulate",
    tags=["payments"],
    summary="Simular pagamento (apenas dev mode)",
    description="""
    Simula um pagamento para uma cobrança em modo de desenvolvimento.
    
    **Importante:**
    - Esta rota só funciona para cobranças criadas em modo de desenvolvimento
    - Use apenas para testes
    - Não disponível em produção
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    parameters=[
        OpenApiParameter(
            name="billing_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="ID da cobrança na AbacatePay",
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Pagamento simulado com sucesso",
            examples=[
                OpenApiExample(
                    name="Pagamento simulado",
                    value={
                        "status": "PAID",
                        "billing_id": "bill_12345667",
                        "message": "Payment simulated successfully",
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Cobrança não está em modo de desenvolvimento",
            examples=[
                OpenApiExample(
                    name="Não é dev mode",
                    value={
                        "error": "Simulação de pagamento só está disponível em modo de desenvolvimento",
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description="Cobrança não encontrada",
        ),
    },
)
