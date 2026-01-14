from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from ..serializers.collections import NftCollectionSerializer


collection_list_schema = extend_schema(
    operation_id="collections_list",
    tags=["collections"],
    summary="Listar todas as coleções NFT",
    description="""
    Retorna uma lista de todas as coleções NFT cadastradas no sistema.

    **Funcionalidades:**
    - Listagem completa de coleções
    - Busca por termo (query parameter `q`)
    - Busca em múltiplos campos: nome, descrição, endereço e slug

    **Exemplos de uso:**
    - `/collections/` - Lista todas as coleções
    - `/collections/?q=bored` - Busca coleções com "bored" no nome, descrição, endereço ou slug
    """,
    parameters=[
        OpenApiParameter(
            name="q",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Termo de busca para filtrar coleções por nome, descrição, endereço ou slug",
            required=False,
            examples=[
                OpenApiExample(
                    name="Busca por nome",
                    value="Bored Ape",
                    description="Busca coleções que contenham 'Bored Ape' em qualquer campo",
                ),
                OpenApiExample(
                    name="Busca por endereço",
                    value="0x",
                    description="Busca coleções por endereço Ethereum",
                ),
            ],
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=NftCollectionSerializer(many=True),
            description="Lista de coleções retornada com sucesso",
            examples=[
                OpenApiExample(
                    name="Resposta de Sucesso",
                    value=[
                        {
                            "id": 1,
                            "name": "Bored Ape Yacht Club",
                            "slug": "bored-ape-yacht-club",
                            "description": "Uma coleção de 10.000 NFTs únicos de macacos entediados",
                            "address": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
                            "profile_image": "https://example.com/profile.jpg",
                            "cover_image": "https://example.com/cover.jpg",
                            "creator": 1,
                            "creator_name": "",
                            "author": "admin",
                            "items_count": 10000,
                            "owners_count": 5400,
                            "floor_price": "15.5000",
                            "floor_price_eth": "15.5000 ETH",
                            "total_volume": "620000.00",
                            "total_volume_eth": "620000.00 ETH",
                            "metadata_api_url": "https://api.example.com/metadata",
                            "project_id": 1,
                            "project_owner_address": "",
                            "website_url": "https://boredapeyachtclub.com",
                            "twitter_url": "https://twitter.com/BoredApeYC",
                            "instagram_url": "",
                            "discord_url": "https://discord.gg/bayc",
                            "telegram_url": "",
                            "created_at": "2025-01-15T10:30:00Z",
                            "updated_at": "2025-01-20T15:45:00Z",
                        }
                    ],
                    response_only=True,
                )
            ],
        ),
    },
)

collection_create_schema = extend_schema(
    operation_id="collections_create",
    tags=["collections"],
    summary="Criar nova coleção NFT",
    description="""
    Cria uma nova coleção NFT no sistema.

    **Campos obrigatórios:**
    - `name` - Nome da coleção
    - `address` - Endereço do contrato Ethereum (formato: 0x + 40 caracteres hexadecimais)

    **Campos opcionais:**
    - Imagens: `profile_image`, `cover_image`
    - Criador: `creator` (FK), `creator_name` (alternativo)
    - Estatísticas: `items_count`, `owners_count`, `floor_price`, `total_volume`
    - Site Oficial: `website_url`
    - Redes Sociais: `twitter_url`, `instagram_url`, `discord_url`, `telegram_url`
    - Metadados: `metadata_api_url`, `project_id`, `project_owner_address`

    **Nota:** O campo `slug` é gerado automaticamente a partir do nome.
    """,
    request=NftCollectionSerializer,
    examples=[
        OpenApiExample(
            name="Criar Coleção Completa",
            value={
                "name": "CryptoPunks",
                "description": "10,000 unique collectible characters with proof of ownership stored on the Ethereum blockchain",
                "address": "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB",
                "profile_image": "https://example.com/cryptopunks-profile.jpg",
                "cover_image": "https://example.com/cryptopunks-cover.jpg",
                "creator_name": "Larva Labs",
                "items_count": 10000,
                "owners_count": 3700,
                "floor_price": "45.5",
                "total_volume": "1200000",
                "website_url": "https://cryptopunks.app",
                "twitter_url": "https://twitter.com/cryptopunksnfts",
                "discord_url": "https://discord.gg/cryptopunks",
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Criar Coleção Básica",
            value={
                "name": "My NFT Collection",
                "address": "0x1234567890123456789012345678901234567890",
                "description": "Uma coleção incrível de NFTs",
            },
            request_only=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=NftCollectionSerializer,
            description="Coleção criada com sucesso",
        ),
        400: OpenApiResponse(
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Erro de Validação - Endereço Inválido",
                    value={
                        "address": [
                            "Endereço Ethereum inválido. Esperado: 0x + 40 hex."
                        ]
                    },
                ),
                OpenApiExample(
                    name="Erro de Validação - Endereço Duplicado",
                    value={
                        "address": [
                            "nft collection com este endereço do contrato já existe."
                        ]
                    },
                ),
            ],
        ),
    },
)

collection_detail_schema = extend_schema(
    operation_id="collections_detail",
    tags=["collections"],
    summary="Obter detalhes de uma coleção NFT",
    description="""
    Retorna os detalhes completos de uma coleção NFT específica.

    **Identificação:**
    - A coleção é identificada pelo `slug` (gerado automaticamente a partir do nome)

    **Retorna:**
    - Todas as informações da coleção
    - Dados do criador
    - Estatísticas (itens, proprietários, floor price, volume total)
    - Links sociais e metadados
    """,
    responses={
        200: OpenApiResponse(
            response=NftCollectionSerializer,
            description="Detalhes da coleção retornados com sucesso",
        ),
        404: OpenApiResponse(
            description="Coleção não encontrada",
            examples=[
                OpenApiExample(
                    name="Coleção não encontrada",
                    value={"detail": "Not found."},
                )
            ],
        ),
    },
)

collection_update_schema = extend_schema(
    operation_id="collections_update",
    tags=["collections"],
    summary="Atualizar completamente uma coleção NFT",
    description="""
    Atualiza completamente uma coleção NFT existente (PUT).

    **Atenção:**
    - PUT requer todos os campos obrigatórios
    - Use PATCH para atualização parcial

    **Campos obrigatórios:**
    - `name` - Nome da coleção
    - `address` - Endereço do contrato
    """,
    request=NftCollectionSerializer,
    examples=[
        OpenApiExample(
            name="Atualizar Coleção",
            value={
                "name": "Bored Ape Yacht Club - Updated",
                "description": "Descrição atualizada da coleção",
                "address": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
                "items_count": 10000,
                "owners_count": 5500,
                "floor_price": "16.2",
                "total_volume": "650000",
            },
            request_only=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=NftCollectionSerializer,
            description="Coleção atualizada com sucesso",
        ),
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Coleção não encontrada"),
    },
)

collection_partial_update_schema = extend_schema(
    operation_id="collections_partial_update",
    tags=["collections"],
    summary="Atualizar parcialmente uma coleção NFT",
    description="""
    Atualiza parcialmente uma coleção NFT existente (PATCH).

    **Vantagens:**
    - Atualiza apenas os campos enviados
    - Não requer campos obrigatórios
    - Ideal para atualizar estatísticas ou links

    **Casos de uso comuns:**
    - Atualizar estatísticas (floor price, volume, contagem)
    - Adicionar ou modificar links sociais
    - Atualizar imagens
    """,
    request=NftCollectionSerializer,
    examples=[
        OpenApiExample(
            name="Atualizar Estatísticas",
            value={
                "floor_price": "18.5",
                "total_volume": "700000",
                "owners_count": 5600,
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Atualizar Links Sociais",
            value={
                "twitter_url": "https://twitter.com/new_handle",
                "discord_url": "https://discord.gg/newserver",
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Atualizar Imagens",
            value={
                "profile_image": "https://example.com/new-profile.jpg",
                "cover_image": "https://example.com/new-cover.jpg",
            },
            request_only=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=NftCollectionSerializer,
            description="Coleção atualizada com sucesso",
        ),
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Coleção não encontrada"),
    },
)

collection_delete_schema = extend_schema(
    operation_id="collections_delete",
    tags=["collections"],
    summary="Deletar uma coleção NFT",
    description="""
    Remove permanentemente uma coleção NFT do sistema.

    **Atenção:**
    - Esta ação é irreversível
    - Todos os dados da coleção serão perdidos
    - Use com cautela
    """,
    responses={
        204: OpenApiResponse(description="Coleção deletada com sucesso (sem conteúdo)"),
        404: OpenApiResponse(
            description="Coleção não encontrada",
            examples=[
                OpenApiExample(
                    name="Coleção não encontrada",
                    value={"detail": "Not found."},
                )
            ],
        ),
    },
)

collection_stats_schema = extend_schema(
    operation_id="collections_stats",
    tags=["collections"],
    summary="Obter estatísticas gerais das coleções",
    description="""
    Retorna estatísticas agregadas de todas as coleções NFT no sistema.

    **Métricas incluídas:**
    - Total de coleções
    - Total de itens (NFTs) em todas as coleções
    - Total de proprietários únicos
    - Preço médio de floor price
    - Volume total negociado

    **Casos de uso:**
    - Dashboard administrativo
    - Página de estatísticas públicas
    - Análise de mercado
    """,
    responses={
        200: OpenApiResponse(
            description="Estatísticas retornadas com sucesso",
            examples=[
                OpenApiExample(
                    name="Estatísticas",
                    value={
                        "total_collections": 150,
                        "total_items": 2500000,
                        "total_owners": 450000,
                        "average_floor_price": 1.85,
                        "total_volume": 15000000.50,
                    },
                )
            ],
        ),
    },
)

collection_trending_schema = extend_schema(
    operation_id="collections_trending",
    tags=["collections"],
    summary="Obter coleções em alta (trending)",
    description="""
    Retorna as coleções NFT com maior volume de negociação.

    **Ordenação:**
    - Ordenadas por volume total em ordem decrescente
    - Apenas coleções com volume > 0

    **Parâmetros:**
    - `limit` - Número máximo de coleções a retornar (padrão: 10)

    **Casos de uso:**
    - Página inicial - seção de trending
    - Rankings de coleções
    - Análise de mercado
    """,
    parameters=[
        OpenApiParameter(
            name="limit",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Número máximo de coleções trending a retornar",
            required=False,
            default=10,
            examples=[
                OpenApiExample(
                    name="Top 5",
                    value=5,
                ),
                OpenApiExample(
                    name="Top 20",
                    value=20,
                ),
            ],
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=NftCollectionSerializer(many=True),
            description="Lista de coleções trending retornada com sucesso",
        ),
    },
)

# Serializer para documentação da rota de criação via JSON
CollectionCreateRequestSerializer = inline_serializer(
    name="CollectionCreateRequest",
    fields={
        "address": serializers.CharField(
            help_text="Endereço do contrato Ethereum (obrigatório, formato: 0x + 40 hex)",
            required=True,
        ),
        "name": serializers.CharField(
            help_text="Nome da coleção",
            required=False,
        ),
        "description": serializers.CharField(
            help_text="Descrição da coleção",
            required=False,
        ),
        "icon_url": serializers.URLField(
            help_text="URL da imagem de perfil (será mapeado para profile_image)",
            required=False,
        ),
        "collection_image_url": serializers.URLField(
            help_text="URL da imagem de capa (será mapeado para cover_image)",
            required=False,
        ),
        "project_id": serializers.IntegerField(
            help_text="ID do projeto",
            required=False,
        ),
        "project_owner_address": serializers.CharField(
            help_text="Endereço do proprietário do projeto (formato: 0x + 40 hex)",
            required=False,
        ),
        "metadata_api_url": serializers.URLField(
            help_text="URL da API de metadados",
            required=False,
        ),
        "creator_name": serializers.CharField(
            help_text="Nome do criador da coleção",
            required=False,
        ),
        "items_count": serializers.IntegerField(
            help_text="Número total de itens na coleção",
            required=False,
        ),
        "owners_count": serializers.IntegerField(
            help_text="Número total de proprietários únicos",
            required=False,
        ),
        "floor_price": serializers.DecimalField(
            help_text="Preço mínimo da coleção em ETH",
            required=False,
            max_digits=20,
            decimal_places=8,
        ),
        "total_volume": serializers.DecimalField(
            help_text="Volume total negociado em ETH",
            required=False,
            max_digits=30,
            decimal_places=8,
        ),
        "website_url": serializers.URLField(
            help_text="URL do site oficial",
            required=False,
        ),
        "twitter_url": serializers.URLField(
            help_text="URL do Twitter/X",
            required=False,
        ),
        "instagram_url": serializers.URLField(
            help_text="URL do Instagram",
            required=False,
        ),
        "discord_url": serializers.URLField(
            help_text="URL do Discord",
            required=False,
        ),
        "telegram_url": serializers.URLField(
            help_text="URL do Telegram",
            required=False,
        ),
        "created_at": serializers.DateTimeField(
            help_text="Data de criação (ignorado, usado apenas para referência)",
            required=False,
        ),
        "updated_at": serializers.DateTimeField(
            help_text="Data de atualização (ignorado, usado apenas para referência)",
            required=False,
        ),
    },
)

collection_create_from_json_schema = extend_schema(
    operation_id="collections_create_from_json",
    tags=["collections"],
    summary="Criar ou atualizar coleção NFT via JSON (Superuser apenas)",
    description="Cria ou atualiza uma coleção NFT. Requer autenticação de superuser.",
    request=CollectionCreateRequestSerializer,
    examples=[
        OpenApiExample(
            name="Exemplo completo (Habbo Furni)",
            value={
                "address": "0xec4de0a00c694cc7957fb90b9005b24a3f4f8b99",
                "name": "Habbo Furni",
                "description": "Habbo NFT Furni that you can use in Habbo",
                "icon_url": "https://nft-tokens.habbo.com/items/furnicollection-icon.png",
                "collection_image_url": "https://nft-tokens.habbo.com/items/furnicollectionV2.png",
                "project_id": 10025,
                "project_owner_address": "0x1d1c83bc7130ac927ebea2c73bbe723ab2e3dfc0",
                "metadata_api_url": "https://nft-tokens.habbo.com/items/metadata",
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Exemplo básico",
            value={
                "address": "0x1234567890123456789012345678901234567890",
                "name": "Minha Coleção NFT",
                "description": "Uma coleção incrível",
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Exemplo com estatísticas",
            value={
                "address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                "name": "Coleção Popular",
                "description": "Coleção com muitas estatísticas",
                "icon_url": "https://example.com/icon.png",
                "collection_image_url": "https://example.com/cover.png",
                "items_count": 10000,
                "owners_count": 3500,
                "floor_price": "25.5",
                "total_volume": "500000.0",
                "website_url": "https://example.com",
                "twitter_url": "https://twitter.com/example",
            },
            request_only=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=NftCollectionSerializer,
            description="Coleção criada com sucesso",
            examples=[
                OpenApiExample(
                    name="Coleção criada",
                    value={
                        "id": 1,
                        "name": "Habbo Furni",
                        "slug": "habbo-furni",
                        "description": "Habbo NFT Furni that you can use in Habbo",
                        "address": "0xec4de0a00c694cc7957fb90b9005b24a3f4f8b99",
                        "profile_image": "https://nft-tokens.habbo.com/items/furnicollection-icon.png",
                        "cover_image": "https://nft-tokens.habbo.com/items/furnicollectionV2.png",
                        "creator": None,
                        "creator_name": "",
                        "author": "Desconhecido",
                        "items_count": 0,
                        "owners_count": 0,
                        "floor_price": "0.00000000",
                        "floor_price_eth": "0.0000 ETH",
                        "total_volume": "0.00000000",
                        "total_volume_eth": "0.00 ETH",
                        "metadata_api_url": "https://nft-tokens.habbo.com/items/metadata",
                        "project_id": 10025,
                        "project_owner_address": "0x1d1c83bc7130ac927ebea2c73bbe723ab2e3dfc0",
                        "website_url": "",
                        "twitter_url": "",
                        "instagram_url": "",
                        "discord_url": "",
                        "telegram_url": "",
                        "created_at": "2025-12-25T02:00:00Z",
                        "updated_at": "2025-12-25T02:00:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        200: OpenApiResponse(
            response=NftCollectionSerializer,
            description="Coleção atualizada com sucesso",
        ),
        400: OpenApiResponse(
            description="Erro de validação",
            examples=[
                OpenApiExample(
                    name="Campo address obrigatório",
                    value={"detail": "Campo 'address' é obrigatório."},
                ),
                OpenApiExample(
                    name="Endereço Ethereum inválido",
                    value={
                        "address": [
                            "Endereço Ethereum inválido. Esperado: 0x + 40 hex."
                        ]
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Não autenticado",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={"detail": "Authentication credentials were not provided."},
                ),
            ],
        ),
        403: OpenApiResponse(
            description="Acesso negado - requer superuser",
            examples=[
                OpenApiExample(
                    name="Não é superuser",
                    value={"detail": "Apenas superusers podem criar coleções."},
                ),
            ],
        ),
    },
)
