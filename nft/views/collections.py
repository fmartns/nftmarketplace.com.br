from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.permissions import AllowAny, IsAdminUser
from decimal import Decimal

from ..models import NftCollection
from ..serializers.collections import NftCollectionSerializer
from ..docs.collections import (
    collection_list_schema,
    collection_detail_schema,
    collection_stats_schema,
    collection_trending_schema,
    collection_create_from_json_schema,
)


class CollectionListCreateAPIView(APIView):
    """
    API para listar e criar coleções NFT.

    GET: Lista todas as coleções com opção de busca
    POST: Cria uma nova coleção
    """

    permission_classes = [AllowAny]
    serializer_class = NftCollectionSerializer

    @collection_list_schema
    def get(self, request):
        """Lista todas as coleções NFT com suporte a busca."""
        q = request.query_params.get("q")
        qs = NftCollection.objects.all()

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(address__icontains=q)
                | Q(slug__icontains=q)
                | Q(creator_name__icontains=q)
            )

        qs = qs.order_by("-created_at")
        serializer = NftCollectionSerializer(qs, many=True)
        return Response(serializer.data)


class CollectionDetailAPIView(APIView):
    """
    API para operações com uma coleção NFT específica.
    """

    permission_classes = [AllowAny]
    serializer_class = NftCollectionSerializer

    def get_object(self, slug):
        """Retorna uma coleção pelo slug ou retorna 404."""
        return get_object_or_404(NftCollection, slug=slug)

    @collection_detail_schema
    def get(self, request, slug):
        """Retorna os detalhes completos de uma coleção NFT."""
        obj = self.get_object(slug)
        return Response(NftCollectionSerializer(obj).data)


class CollectionStatsAPIView(APIView):
    """
    API para obter estatísticas gerais das coleções.
    """

    @collection_stats_schema
    def get(self, request):
        """Retorna estatísticas agregadas de todas as coleções."""
        from django.db.models import Sum, Avg

        collections = NftCollection.objects.all()

        stats = {
            "total_collections": collections.count(),
            "total_items": collections.aggregate(Sum("items_count"))["items_count__sum"]
            or 0,
            "total_owners": collections.aggregate(Sum("owners_count"))[
                "owners_count__sum"
            ]
            or 0,
            "average_floor_price": float(
                collections.aggregate(Avg("floor_price"))["floor_price__avg"] or 0
            ),
            "total_volume": float(
                collections.aggregate(Sum("total_volume"))["total_volume__sum"] or 0
            ),
        }

        return Response(stats)


class CollectionTrendingAPIView(APIView):
    """
    API para obter coleções em alta (trending).
    Ordenadas por volume total em ordem decrescente.
    """

    @collection_trending_schema
    def get(self, request):
        """Retorna as coleções trending ordenadas por volume total."""
        limit = int(request.query_params.get("limit", 10))

        trending = NftCollection.objects.filter(total_volume__gt=0).order_by(
            "-total_volume"
        )[:limit]

        serializer = NftCollectionSerializer(trending, many=True)
        return Response(serializer.data)


class CollectionCreateAPIView(APIView):
    """
    API para criar coleções NFT (apenas superusers).
    Aceita JSON no formato específico com campos como icon_url e collection_image_url.
    """

    permission_classes = [IsAdminUser]

    @collection_create_from_json_schema
    def post(self, request):
        """Cria ou atualiza uma coleção NFT a partir de JSON."""
        if not request.user.is_superuser:
            return Response(
                {"detail": "Apenas superusers podem criar coleções."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data
        address = data.get("address", "").strip()

        if not address:
            return Response(
                {"detail": "Campo 'address' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mapear campos do JSON para o modelo
        defaults = {}

        # Campos simples
        if "name" in data:
            defaults["name"] = data["name"]
        if "description" in data:
            defaults["description"] = data.get("description", "")

        # Mapear campos de imagem (com fallback)
        profile_image = data.get("icon_url") or data.get("profile_image")
        cover_image = data.get("collection_image_url") or data.get("cover_image")
        if profile_image:
            defaults["profile_image"] = profile_image
        if cover_image:
            defaults["cover_image"] = cover_image

        # Campos opcionais
        if "metadata_api_url" in data:
            defaults["metadata_api_url"] = data.get("metadata_api_url", "")
        if "project_id" in data:
            defaults["project_id"] = data.get("project_id")
        if "project_owner_address" in data:
            defaults["project_owner_address"] = data.get("project_owner_address", "")
        if "creator_name" in data:
            defaults["creator_name"] = data.get("creator_name", "")

        # Campos numéricos
        if "items_count" in data:
            try:
                defaults["items_count"] = int(data["items_count"])
            except (ValueError, TypeError):
                pass

        if "owners_count" in data:
            try:
                defaults["owners_count"] = int(data["owners_count"])
            except (ValueError, TypeError):
                pass

        if "floor_price" in data:
            try:
                defaults["floor_price"] = Decimal(str(data["floor_price"]))
            except (ValueError, TypeError):
                pass

        if "total_volume" in data:
            try:
                defaults["total_volume"] = Decimal(str(data["total_volume"]))
            except (ValueError, TypeError):
                pass

        # URLs de redes sociais (se fornecidas)
        url_fields = [
            "website_url",
            "twitter_url",
            "instagram_url",
            "discord_url",
            "telegram_url",
        ]
        for field in url_fields:
            if field in data:
                defaults[field] = data.get(field, "")

        # Criar ou atualizar a coleção
        collection, created = NftCollection.objects.update_or_create(
            address=address,
            defaults=defaults,
        )

        serializer = NftCollectionSerializer(collection)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
