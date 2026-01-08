"""
Views para pedidos
"""
from decimal import Decimal
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from django.utils import timezone

from ..models import Order, OrderItem, Coupon
from ..serializers import OrderSerializer, OrderCreateSerializer
from ..payment.stripe_service import StripeService


class OrderListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar pedidos
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """Retorna apenas os pedidos do usuário autenticado"""
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items", "coupon"
        ).order_by("-created_at")
    
    @extend_schema(
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
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        operation_id="orders_create",
        tags=["orders"],
        summary="Criar novo pedido",
        description="""
        Cria um novo pedido com itens (legacy ou NFT).
        
        **Processo:**
        1. Valida os itens e calcula o subtotal
        2. Aplica cupom de desconto (se fornecido)
        3. Calcula o total final
        4. Cria PaymentIntent no Stripe
        5. Retorna os dados do pedido com client_secret para pagamento
        
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
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Cria um novo pedido"""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        items_data = validated_data["items"]
        coupon_code = validated_data.get("coupon_code")
        notes = validated_data.get("notes", "")
        
        # Calcula subtotal
        subtotal = Decimal("0.00")
        for item_data in items_data:
            unit_price = item_data["unit_price"]
            quantity = item_data["quantity"]
            subtotal += unit_price * quantity
        
        # Aplica cupom se fornecido
        coupon = None
        discount_amount = Decimal("0.00")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                discount_amount = coupon.calculate_discount(subtotal)
                # Incrementa contador de usos
                coupon.uses_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass
        
        # Calcula total
        total = subtotal - discount_amount
        if total < Decimal("0.01"):
            return Response(
                {"error": "Valor total do pedido deve ser maior que R$ 0,01."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Cria o pedido
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total=total,
            coupon=coupon,
            notes=notes,
            status="pending",
        )
        
        # Cria os itens do pedido
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                content_type=item_data["content_type"],
                object_id=item_data["object_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
            )
        
        # Cria PaymentIntent no Stripe
        try:
            payment_data = StripeService.create_payment_intent(
                amount=total,
                currency="brl",
                metadata={
                    "order_id": order.order_id,
                    "user_id": str(request.user.id),
                },
            )
            
            order.stripe_payment_intent_id = payment_data["payment_intent_id"]
            order.stripe_client_secret = payment_data["client_secret"]
            order.save()
        
        except Exception as e:
            # Se falhar ao criar PaymentIntent, mantém o pedido mas sem pagamento
            # O admin pode marcar como pago manualmente
            pass
        
        # Retorna o pedido criado
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    """
    View para detalhes de um pedido
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = "order_id"
    lookup_url_kwarg = "order_id"
    
    def get_queryset(self):
        """Retorna apenas os pedidos do usuário autenticado"""
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items", "coupon"
        )
    
    @extend_schema(
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
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)





