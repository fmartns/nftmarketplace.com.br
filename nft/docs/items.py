from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
)

from ..serializers.items import FetchByProductCodeSerializer, NFTItemSerializer


nft_item_upsert_schema = extend_schema(
    operation_id="nft_items_upsert",
    tags=["nft"],
    summary="Cria ou atualiza item pelo menor preço",
    description=(
        "Envia um product_code; o servidor consulta a Immutable, encontra o menor preço, "
        "converte para ETH/USD/BRL e salva via update_or_create. Retorna o item atualizado. "
        "Requisito: a coleção (contrato) correspondente deve estar cadastrada previamente; "
        "caso contrário, a requisição será rejeitada com HTTP 400."
    ),
    request=FetchByProductCodeSerializer,
    responses={
        200: OpenApiResponse(response=NFTItemSerializer, description="Item atualizado"),
        201: OpenApiResponse(response=NFTItemSerializer, description="Item criado"),
        400: OpenApiResponse(
            description="Erro de validação / rate limit / coleção ausente"
        ),
        502: OpenApiResponse(description="Falha ao consultar a Immutable"),
    },
    examples=[
        OpenApiExample(
            "Exemplo de requisição",
            value={"product_code": "nft_cf25_leather"},
            request_only=True,
        ),
        OpenApiExample(
            "Exemplo de resposta",
            value={
                "id": 1,
                "type": "unknown",
                "blueprint": "",
                "image_url": "https://nft-tokens.habbo.com/items/images/nft_cf25_leather.png",
                "name": "Leather",
                "source": "immutable_bids",
                "is_crafted_item": False,
                "is_craft_material": False,
                "rarity": "",
                "item_type": "",
                "item_sub_type": "",
                "number": None,
                "product_code": "nft_cf25_leather",
                "product_type": "",
                "material": "",
                "last_price_eth": "0.012345678900000000",
                "last_price_usd": "23.45",
                "last_price_brl": "123.45",
                "created_at": "2025-10-18T01:32:14.786137-03:00",
                "updated_at": "2025-10-18T01:35:01.000000-03:00",
            },
            response_only=True,
        ),
    ],
)


nft_item_list_schema = extend_schema(
    operation_id="nft_items_list",
    tags=["nft"],
    summary="Lista NFTs com filtros e busca",
    description=(
        "Retorna uma lista paginada de NFTs com suporte a filtros, busca e ordenação.\n\n"
        "Filtros suportados (query params):\n"
        "- rarity (iexact)\n"
        "- item_type (iexact)\n"
        "- item_sub_type (iexact)\n"
        "- material (iexact)\n"
        "- source (iexact)\n"
        "- is_crafted_item (boolean)\n"
        "- is_craft_material (boolean)\n"
        "- min_price_brl (number)\n"
        "- max_price_brl (number)\n"
        "- collection_id (number)\n"
        "- collection_slug (string)\n"
        "Busca: "
        "use o parâmetro 'search' para procurar por nome ou product_code.\n"
        "Ordenação: use 'ordering', ex.: ordering=last_price_brl,-updated_at."
    ),
    parameters=[
        OpenApiParameter(name="rarity", type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="item_type", type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(
            name="item_sub_type", type=str, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(name="material", type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="source", type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(
            name="is_crafted_item", type=bool, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="is_craft_material", type=bool, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="min_price_brl", type=float, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="max_price_brl", type=float, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="collection_id", type=int, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="collection_slug", type=str, location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(name="search", type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="ordering", type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="page_size", type=int, location=OpenApiParameter.QUERY),
    ],
    responses={200: OpenApiResponse(response=NFTItemSerializer)},
    examples=[
        OpenApiExample(
            "Exemplo de listagem",
            value={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "Leather",
                        "product_code": "nft_cf25_leather",
                        "rarity": "",
                        "item_type": "",
                        "item_sub_type": "",
                        "last_price_brl": "123.45",
                        "updated_at": "2025-10-18T01:35:01-03:00",
                    }
                ],
            },
            response_only=True,
        )
    ],
)









