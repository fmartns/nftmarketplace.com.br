from rest_framework import permissions, status, generics, filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from .docs.items import nft_item_upsert_schema, nft_item_list_schema

from django.db.models import Count, Max
from django.utils import timezone
from datetime import timedelta
from .models import NFTItem, PricingConfig
from .serializers.items import (
    NFTItemSerializer,
    FetchByProductCodeSerializer,
    PricingConfigSerializer,
)
from .services import (
    fetch_item_from_immutable,
    ImmutableAPIError,
    fetch_7d_sales_stats,
    fetch_min_listing_prices,
)
from rest_framework.permissions import AllowAny
from .filters import NFTItemFilter
from nft.models import NftCollection


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    pass


class NFTItemUpsertAPI(APIView):
    permission_classes = [AllowAny]

    @nft_item_upsert_schema
    def post(self, request):
        serializer = FetchByProductCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_code = serializer.validated_data["product_code"]

        try:
            mapped, collection_address = fetch_item_from_immutable(product_code)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ImmutableAPIError:
            return Response(
                {"detail": "Falha ao consultar a Immutable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"detail": "Falha ao consultar a Immutable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Resolve the collection: by contract address if available, or from existing item
        existing_item = (
            NFTItem.objects.filter(product_code=product_code)
            .only("id", "collection_id")
            .first()
        )
        collection_obj = None
        if collection_address:
            collection_obj = NftCollection.objects.filter(
                address__iexact=collection_address
            ).first()
        if not collection_obj and existing_item and existing_item.collection_id:
            # Keep previously linked collection if present
            try:
                collection_obj = NftCollection.objects.filter(
                    id=existing_item.collection_id
                ).first()
            except Exception:
                collection_obj = None

        if not collection_obj:
            # Block the POST if we don't have a collection for this product
            msg = "Coleção não cadastrada para este produto. Cadastre a coleção (contrato) antes de enviar o product_code."
            if collection_address:
                msg = (
                    "Coleção não cadastrada para o contrato informado: "
                    f"{collection_address}. Cadastre a coleção antes de enviar o product_code."
                )
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        # Compute 7d sales metrics (best-effort)
        try:
            seven_d = fetch_7d_sales_stats(product_code)
        except Exception:
            seven_d = {}

        # Ensure the saved price matches the product page display logic (minimum listing)
        try:
            min_prices = fetch_min_listing_prices(product_code)
        except Exception:
            min_prices = None

        if min_prices is not None:
            pe, pu, pb = min_prices
            # override only price fields to mirror frontend
            mapped["last_price_eth"] = pe
            mapped["last_price_usd"] = pu
            mapped["last_price_brl"] = pb

        # Proceed with upsert, binding collection and 7d metrics
        defaults = {**mapped, **seven_d, "collection": collection_obj}
        obj, created = NFTItem.objects.update_or_create(
            product_code=product_code,
            defaults=defaults,
        )
        out = NFTItemSerializer(obj)
        return Response(
            out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class NFTItemListAPI(generics.ListAPIView):
    queryset = NFTItem.objects.all()
    serializer_class = NFTItemSerializer
    permission_classes = [AllowAny]
    filterset_class = NFTItemFilter
    # Enable filtering, search and ordering backends
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    # Include both English (name) and Portuguese (name_pt_br) for search
    search_fields = ["name", "name_pt_br", "product_code"]
    ordering_fields = [
        "name",
        "rarity",
        "item_type",
        "item_sub_type",
        "last_price_brl",
        "updated_at",
        "created_at",
        # 7-day metrics for trending and top sections
        "seven_day_sales_count",
        "seven_day_volume_brl",
        "seven_day_avg_price_brl",
        "seven_day_last_sale_brl",
        "seven_day_price_change_pct",
    ]

    @nft_item_list_schema
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        # Hard-enforce promo_only even if filters are misconfigured on some environments
        val = self.request.query_params.get("promo_only")
        truthy = {"1", "true", "t", "yes", "y", "on"}
        apply = False
        if val is not None:
            apply = str(val).strip().lower() in truthy
        if apply:
            from decimal import Decimal

            cfg = (
                PricingConfig.objects.order_by("-updated_at")
                .only("global_markup_percent")
                .first()
            )
            global_markup = (
                cfg.global_markup_percent
                if cfg and cfg.global_markup_percent is not None
                else Decimal("30.00")
            )
            qs = qs.filter(
                markup_percent__isnull=False, markup_percent__lt=global_markup
            )
        return qs


class PricingConfigAPI(APIView):
    """
    API para obter a configuração de markup global
    """

    permission_classes = [AllowAny]

    def get(self, request):
        try:
            config = PricingConfig.objects.order_by("-updated_at").first()
            if not config:
                # Return default if no config exists
                config = PricingConfig(global_markup_percent=30.00)

            serializer = PricingConfigSerializer(config)
            return Response(serializer.data)
        except Exception:
            return Response(
                {"error": "Erro ao buscar configuração de markup"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TrendingByAccessAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 4))
        days = int(request.query_params.get("days", 7))
        cutoff = timezone.now() - timedelta(days=days)

        # Get top items by access count in the last N days
        top_items = (
            NFTItem.objects.filter(
                access_records__accessed_at__gte=cutoff,
            )
            .annotate(
                access_count=Count("access_records"),
                last_access=Max("access_records__accessed_at"),
            )
            .filter(access_count__gt=0)
            .order_by("-access_count", "-last_access")[:limit]
        )

        serializer = NFTItemSerializer(top_items, many=True)
        return Response({"results": serializer.data})
