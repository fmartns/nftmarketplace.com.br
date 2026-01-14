"""
Views para pedidos
"""

from decimal import Decimal
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import Order, OrderItem, Coupon
from ..serializers import OrderSerializer, OrderCreateSerializer
from ..docs import (
    orders_list_schema,
    orders_create_schema,
    orders_detail_schema,
)


class OrderListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar pedidos
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        """Retorna apenas os pedidos do usuário autenticado"""
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items", "coupon")
            .order_by("-created_at")
        )

    @orders_list_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @orders_create_schema
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

        # Pagamento será processado via AbacatePay (criar billing separadamente)

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

    def get_object(self):
        """
        Override para decodificar o order_id da URL corretamente
        """
        from urllib.parse import unquote
        from rest_framework.exceptions import NotFound

        order_id = self.kwargs.get(self.lookup_url_kwarg)

        if order_id:
            order_id = unquote(order_id)
            if not order_id.startswith("#"):
                order_id = f"#{order_id}"

        queryset = self.get_queryset()
        try:
            obj = queryset.get(order_id=order_id)
            return obj
        except Order.DoesNotExist:
            raise NotFound(f"Pedido com ID '{order_id}' não encontrado.")

    @orders_detail_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
