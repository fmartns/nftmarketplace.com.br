"""
Documentação das rotas de clientes AbacatePay.
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from ..serializers.customer import CustomerSerializer


customer_create_schema = extend_schema(
    operation_id="customer_create",
    tags=["payments"],
    summary="Criar cliente na AbacatePay",
    description="""
    Cria um cliente na AbacatePay para o usuário autenticado.
    
    **Processo:**
    1. Verifica se o usuário já possui um cliente
    2. Se não existir, cria na API da AbacatePay
    3. Salva os dados no banco de dados
    
    **Nota:** O cliente é criado automaticamente quando você cria uma cobrança.
    Esta rota é útil se você quiser criar o cliente antecipadamente.
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    responses={
        201: OpenApiResponse(
            response=CustomerSerializer,
            description="Cliente criado com sucesso",
            examples=[
                OpenApiExample(
                    name="Cliente criado",
                    value={
                        "id": 1,
                        "external_id": "cust_12345",
                        "user": 1,
                        "user_email": "[email protected]",
                        "user_username": "usuario123",
                        "metadata": {
                            "user_id": "1",
                            "username": "usuario123",
                            "email": "[email protected]",
                        },
                        "created_at": "2024-01-20T14:30:00Z",
                        "updated_at": "2024-01-20T14:30:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        200: OpenApiResponse(
            description="Cliente já existe",
            examples=[
                OpenApiExample(
                    name="Cliente existente",
                    value={
                        "message": "Cliente já existe",
                        "customer": {
                            "id": 1,
                            "external_id": "cust_12345",
                            "user_email": "[email protected]",
                        },
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="Erro ao criar cliente na AbacatePay",
            examples=[
                OpenApiExample(
                    name="Erro na API",
                    value={
                        "error": "Erro ao criar cliente na AbacatePay",
                        "details": {"message": "Invalid API key"},
                    },
                ),
            ],
        ),
    },
)


customer_list_schema = extend_schema(
    operation_id="customer_list",
    tags=["payments"],
    summary="Listar clientes",
    description="""
    Lista clientes da AbacatePay.
    
    **Permissões:**
    - Usuários comuns: veem apenas seu próprio cliente
    - Administradores: veem todos os clientes
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    responses={
        200: OpenApiResponse(
            response=CustomerSerializer(many=True),
            description="Lista de clientes retornada com sucesso",
            examples=[
                OpenApiExample(
                    name="Lista de clientes",
                    value=[
                        {
                            "id": 1,
                            "external_id": "cust_12345",
                            "user": 1,
                            "user_email": "[email protected]",
                            "user_username": "usuario123",
                            "created_at": "2024-01-20T14:30:00Z",
                        },
                    ],
                    response_only=True,
                ),
            ],
        ),
    },
)
