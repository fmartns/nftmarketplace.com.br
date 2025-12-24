from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from .serializers import LegacyItemDetailsSerializer, LegacyItemCreateSerializer, LegacyItemListSerializer


legacy_item_detail_schema = extend_schema(
    operation_id="legacy_item_detail",
    tags=["legacy"],
    summary="Obter preço atualizado de um item Legacy",
    description="Busca o preço atualizado na API externa e atualiza os dados no banco (se o item existir). Retorna apenas o preço convertido.",
    parameters=[
        OpenApiParameter(
            name="slug",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="Slug do item Legacy (ex: pillow*6, chair*1)",
            required=True,
            examples=[
                OpenApiExample(
                    name="Almofada",
                    value="pillow*6",
                    description="Slug de uma almofada azul",
                ),
                OpenApiExample(
                    name="Cadeira",
                    value="chair*1",
                    description="Slug de uma cadeira",
                ),
            ],
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Preço retornado com sucesso",
            examples=[
                OpenApiExample(
                    name="Resposta de Sucesso",
                    value={
                        "price": 23.0
                    },
                    description="Preço convertido do item",
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Parâmetro slug inválido ou ausente",
            examples=[
                OpenApiExample(
                    name="Slug Ausente",
                    value={
                        "slug": ["Este campo é obrigatório."]
                    },
                ),
                OpenApiExample(
                    name="Slug Vazio",
                    value={
                        "slug": ["Slug parameter is required"]
                    },
                ),
            ],
        ),
        502: OpenApiResponse(
            description="Erro ao buscar dados da API externa ou item não encontrado no banco",
            examples=[
                OpenApiExample(
                    name="Item não encontrado no banco",
                    value={
                        "error": "Item not found"
                    },
                ),
                OpenApiExample(
                    name="Erro na API externa",
                    value={
                        "error": "Failed to fetch data from external API"
                    },
                ),
                OpenApiExample(
                    name="Dados inválidos da API",
                    value={
                        "error": "Error processing API response"
                    },
                ),
            ],
        ),
    },
)


legacy_item_create_schema = extend_schema(
    operation_id="legacy_item_create",
    tags=["legacy"],
    summary="Criar ou atualizar item Legacy completo",
    description="Cria ou atualiza um item Legacy buscando dados da API externa. Retorna o item completo com preços convertidos. Requer autenticação de administrador.",
    request=LegacyItemCreateSerializer,
    examples=[
        OpenApiExample(
            name="Criar Item",
            value={
                "slug": "pillow*6"
            },
            description="Enviar slug no body da requisição",
            request_only=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=LegacyItemCreateSerializer,
            description="Item criado com sucesso",
            examples=[
                OpenApiExample(
                    name="Item Criado",
                    value={
                        "id": 1,
                        "name": "Almofada de Algodão Azul",
                        "description": "Grande, leve e muito macia",
                        "slug": "pillow*6",
                        "last_price": 23.0,
                        "average_price": 21.2,
                        "available_offers": 4,
                        "image_url": "",
                        "created_at": "2025-12-23T03:42:53.176Z",
                        "updated_at": "2025-12-23T03:42:53.176Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        200: OpenApiResponse(
            response=LegacyItemCreateSerializer,
            description="Item atualizado com sucesso",
            examples=[
                OpenApiExample(
                    name="Item Atualizado",
                    value={
                        "id": 1,
                        "name": "Almofada de Algodão Azul",
                        "description": "Grande, leve e muito macia",
                        "slug": "pillow*6",
                        "last_price": 25.0,
                        "average_price": 22.5,
                        "available_offers": 6,
                        "image_url": "",
                        "created_at": "2025-12-23T03:42:53.176Z",
                        "updated_at": "2025-12-23T04:15:30.200Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Parâmetro slug inválido ou ausente",
            examples=[
                OpenApiExample(
                    name="Slug Ausente",
                    value={
                        "slug": ["Este campo é obrigatório."]
                    },
                ),
                OpenApiExample(
                    name="Slug Vazio",
                    value={
                        "slug": ["Slug parameter is required"]
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Não autenticado - requer autenticação de administrador",
            examples=[
                OpenApiExample(
                    name="Não Autenticado",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
            ],
        ),
        403: OpenApiResponse(
            description="Sem permissão - requer permissão de administrador",
            examples=[
                OpenApiExample(
                    name="Sem Permissão",
                    value={
                        "detail": "Você não tem permissão para executar essa ação."
                    },
                ),
            ],
        ),
        502: OpenApiResponse(
            description="Erro ao buscar dados da API externa",
            examples=[
                OpenApiExample(
                    name="Erro na API Externa",
                    value={
                        "error": "Failed to fetch data from external API"
                    },
                ),
                OpenApiExample(
                    name="Dados Inválidos",
                    value={
                        "error": "Error processing API response"
                    },
                ),
                OpenApiExample(
                    name="Item não encontrado na API",
                    value={
                        "error": "Item data not found in API response"
                    },
                ),
            ],
        ),
    },
)


legacy_item_list_schema = extend_schema(
    operation_id="legacy_item_list",
    tags=["legacy"],
    summary="Listar itens Legacy",
    description="Lista itens Legacy com filtros, ordenação e paginação. Retorna apenas campos essenciais: name, slug, last_price, average_price e available_offers.",
    parameters=[
        OpenApiParameter(
            name="name",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtrar por nome (busca parcial, case-insensitive)",
            required=False,
        ),
        OpenApiParameter(
            name="slug",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtrar por slug (busca parcial, case-insensitive)",
            required=False,
        ),
        OpenApiParameter(
            name="min_price",
            type=OpenApiTypes.NUMBER,
            location=OpenApiParameter.QUERY,
            description="Filtrar por preço mínimo (last_price >= min_price)",
            required=False,
        ),
        OpenApiParameter(
            name="max_price",
            type=OpenApiTypes.NUMBER,
            location=OpenApiParameter.QUERY,
            description="Filtrar por preço máximo (last_price <= max_price)",
            required=False,
        ),
        OpenApiParameter(
            name="min_offers",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filtrar por ofertas disponíveis mínimas (available_offers >= min_offers)",
            required=False,
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Campo para ordenação. Use prefixo '-' para ordem descendente. Campos disponíveis: name, slug, last_price, average_price, available_offers, created_at, updated_at. Padrão: name",
            required=False,
            examples=[
                OpenApiExample(
                    name="Ordenar por nome (crescente)",
                    value="name",
                ),
                OpenApiExample(
                    name="Ordenar por preço (decrescente)",
                    value="-last_price",
                ),
                OpenApiExample(
                    name="Ordenar por ofertas (crescente)",
                    value="available_offers",
                ),
            ],
        ),
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Número da página (padrão: 1)",
            required=False,
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Itens por página (padrão: 20, máximo: 100)",
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=LegacyItemListSerializer,
            description="Lista de itens retornada com sucesso",
            examples=[
                OpenApiExample(
                    name="Resposta Paginada",
                    value={
                        "count": 150,
                        "next": "http://api.example.com/legacy/?page=2&page_size=20",
                        "previous": None,
                        "results": [
                            {
                                "name": "Almofada de Algodão Azul",
                                "slug": "pillow*6",
                                "last_price": 23.0,
                                "average_price": 21.2,
                                "available_offers": 4,
                            },
                            {
                                "name": "Cadeira",
                                "slug": "chair*1",
                                "last_price": 15.5,
                                "average_price": 14.8,
                                "available_offers": 2,
                            },
                        ],
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)

