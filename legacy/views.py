from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
from django.db.models import Q
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from .serializers import LegacyItemDetailsSerializer, LegacyItemCreateSerializer, LegacyItemListSerializer
from .services import LegacyPriceService
from .models import Item
from .docs import legacy_item_detail_schema, legacy_item_create_schema, legacy_item_list_schema


class LegacyItemDetail(APIView):
    permission_classes = [AllowAny]

    @legacy_item_detail_schema
    def get(self, request, slug):
        serializer = LegacyItemDetailsSerializer(data={"slug": slug})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar dados completos da API externa
            item_data = LegacyPriceService.get_item_data(serializer.validated_data["slug"])
            
            # Atualizar item no banco se existir, ou criar se não existir
            item, created = Item.objects.update_or_create(
                slug=item_data["slug"],
                defaults={
                    "name": item_data["name"],
                    "image_url": item_data["image_url"],
                    "description": item_data["description"],
                    "last_price": item_data["last_price"],
                    "average_price": item_data["average_price"],
                    "available_offers": item_data["available_offers"],
                    "price_history": item_data["price_history"],
                }
            )
            
            # Serializar resposta com todos os dados do item
            response_serializer = LegacyItemDetailsSerializer(item)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class LegacyItemCreate(APIView):
    permission_classes = [IsAdminUser]

    @legacy_item_create_schema
    def post(self, request):
        # Obter slug do body da requisição
        slug = request.data.get("slug")
        
        if not slug:
            return Response(
                {"slug": ["Este campo é obrigatório."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        item = Item.objects.filter(slug=slug).first()
        if item:
            return Response(
                {"slug": ["Este item já existe."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        input_serializer = LegacyItemCreateSerializer(data={"slug": slug})
        
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar dados da API externa
            item_data = LegacyPriceService.get_item_data(input_serializer.validated_data["slug"])
            
            # Criar/atualizar item usando o serializer
            item, created = Item.objects.update_or_create(
                slug=item_data["slug"],
                defaults={
                    "name": item_data["name"],
                    "image_url": item_data["image_url"],
                    "description": item_data["description"],
                    "last_price": item_data["last_price"],
                    "average_price": item_data["average_price"],
                    "available_offers": item_data["available_offers"],
                    "price_history": item_data["price_history"],
                }
            )
            
            # Serializar resposta
            response_serializer = LegacyItemCreateSerializer(item)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            
            return Response(response_serializer.data, status=status_code)
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class LegacyItemList(ListAPIView):
    """View para listagem de itens com filtros e paginação"""
    permission_classes = [AllowAny]
    serializer_class = LegacyItemListSerializer
    
    @legacy_item_list_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Item.objects.all()
        
        # Filtro por nome (busca parcial, case-insensitive)
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        # Filtro por slug (busca parcial, case-insensitive)
        slug = self.request.query_params.get('slug', None)
        if slug:
            queryset = queryset.filter(slug__icontains=slug)
        
        # Filtro por preço mínimo
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            try:
                queryset = queryset.filter(last_price__gte=float(min_price))
            except ValueError:
                pass
        
        # Filtro por preço máximo
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            try:
                queryset = queryset.filter(last_price__lte=float(max_price))
            except ValueError:
                pass
        
        # Filtro por ofertas disponíveis mínimas
        min_offers = self.request.query_params.get('min_offers', None)
        if min_offers:
            try:
                queryset = queryset.filter(available_offers__gte=int(min_offers))
            except ValueError:
                pass
        
        # Ordenação
        ordering = self.request.query_params.get('ordering', 'name')
        if ordering.lstrip('-') in ['name', 'slug', 'last_price', 'average_price', 'available_offers', 'created_at', 'updated_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('name')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Customizar resposta com paginação"""
        from rest_framework.pagination import PageNumberPagination
        
        # Configurar paginação
        paginator = PageNumberPagination()
        page_size = request.query_params.get('page_size', '20')
        try:
            paginator.page_size = int(page_size)
        except ValueError:
            paginator.page_size = 20
        
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        
        queryset = self.filter_queryset(self.get_queryset())
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

