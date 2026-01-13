"""
Documentação das rotas de pedidos (Orders).
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from ..serializers import OrderSerializer, OrderCreateSerializer


orders_list_schema = extend_schema(
    operation_id="orders_list",
    tags=["orders"],
    summary="Listar pedidos do usuário",
    description="Retorna a lista de pedidos do usuário autenticado, ordenados pelos mais recentes primeiro.",
    responses={
        200: OpenApiResponse(
            response=OrderSerializer(many=True),
            description="Lista de pedidos retornada com sucesso",
        ),
    },
)


orders_create_schema = extend_schema(
    operation_id="orders_create",
    tags=["orders"],
    summary="Criar novo pedido",
    description="""
    Cria um novo pedido com itens (legacy ou NFT).
    
    **Processo:**
    1. Valida os itens e calcula o subtotal
    2. Aplica cupom de desconto (se fornecido)
    3. Calcula o total final
    4. Retorna os dados do pedido para pagamento via AbacatePay
    
    **Itens:**
    - `item_type`: "legacy" ou "nft"
    - `item_id`: ID do item correspondente
    - `quantity`: Quantidade (padrão: 1)
    """,
    request=OrderCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=OrderSerializer,
            description="Pedido criado com sucesso",
            examples=[
                OpenApiExample(
                    name="Pedido criado com sucesso",
                    value={
                        "id": 1,
                        "order_id": "#ABC123",
                        "user": 1,
                        "status": "pending",
                        "subtotal": "100.00",
                        "discount_amount": "10.00",
                        "total": "90.00",
                        "coupon": None,
                        "paid_at": None,
                        "delivered": False,
                        "delivered_at": None,
                        "items": [
                            {
                                "id": 1,
                                "item_type": "legacy",
                                "item_name": "Item Legacy",
                                "quantity": 1,
                                "unit_price": "100.00",
                                "total_price": "100.00",
                            }
                        ],
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Erro de validação",
                    value={
                        "error": "Item legacy com ID 999 não encontrado.",
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)


orders_detail_schema = extend_schema(
    operation_id="orders_detail",
    tags=["orders"],
    summary="Detalhes de um pedido",
    description="Retorna os detalhes completos de um pedido específico do usuário autenticado.",
    responses={
        200: OpenApiResponse(
            response=OrderSerializer,
            description="Detalhes do pedido retornados com sucesso",
        ),
        404: OpenApiResponse(
            description="Pedido não encontrado",
            examples=[
                OpenApiExample(
                    name="Pedido não encontrado",
                    value={
                        "detail": "Pedido com ID '#ABC123' não encontrado.",
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)
