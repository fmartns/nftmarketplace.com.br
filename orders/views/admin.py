"""
Views administrativas para pedidos e cupons
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from ..models import Order, Coupon
from ..serializers import OrderSerializer, CouponSerializer


class OrderListAdminView(generics.ListAPIView):
    """
    View administrativa para listar todos os pedidos
    """

    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    queryset = (
        Order.objects.all()
        .prefetch_related("items", "coupon", "user")
        .order_by("-created_at")
    )

    @extend_schema(
        operation_id="admin_orders_list",
        tags=["orders", "admin"],
        summary="Listar todos os pedidos (Admin)",
        description="Lista todos os pedidos do sistema. Requer autenticação de administrador.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por status do pedido",
                required=False,
            ),
            OpenApiParameter(
                name="delivered",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar por pedidos entregues (true/false)",
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OrderSerializer(many=True),
                description="Lista de pedidos retornada com sucesso",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Filtros opcionais
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        delivered_filter = request.query_params.get("delivered")
        if delivered_filter is not None:
            delivered = delivered_filter.lower() in ("true", "1", "yes")
            queryset = queryset.filter(delivered=delivered)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrderMarkDeliveredView(APIView):
    """
    View administrativa para marcar pedido como entregue
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="admin_orders_mark_delivered",
        tags=["orders", "admin"],
        summary="Marcar pedido como entregue (Admin)",
        description="Marca um pedido como entregue. Requer autenticação de administrador.",
        responses={
            200: OpenApiResponse(
                response=OrderSerializer,
                description="Pedido marcado como entregue com sucesso",
            ),
            404: OpenApiResponse(
                description="Pedido não encontrado",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Marca um pedido como entregue"""
        order_id = kwargs.get("order_id")
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Pedido não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.delivered:
            return Response(
                {"error": "Pedido já foi marcado como entregue."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.mark_as_delivered(request.user)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CouponAdminView(generics.RetrieveUpdateDestroyAPIView):
    """
    View administrativa para gerenciar cupons (CRUD completo)
    """

    permission_classes = [IsAdminUser]
    serializer_class = CouponSerializer
    queryset = Coupon.objects.all()
    lookup_field = "id"

    @extend_schema(
        operation_id="admin_coupons_detail",
        tags=["orders", "admin"],
        summary="Detalhes de um cupom (Admin)",
        description="Retorna os detalhes de um cupom. Requer autenticação de administrador.",
        responses={
            200: OpenApiResponse(
                response=CouponSerializer,
                description="Detalhes do cupom retornados com sucesso",
            ),
            404: OpenApiResponse(
                description="Cupom não encontrado",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        operation_id="admin_coupons_update",
        tags=["orders", "admin"],
        summary="Atualizar cupom (Admin)",
        description="Atualiza um cupom existente. Requer autenticação de administrador.",
        request=CouponSerializer,
        responses={
            200: OpenApiResponse(
                response=CouponSerializer,
                description="Cupom atualizado com sucesso",
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
            ),
            404: OpenApiResponse(
                description="Cupom não encontrado",
            ),
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        operation_id="admin_coupons_partial_update",
        tags=["orders", "admin"],
        summary="Atualizar parcialmente cupom (Admin)",
        description="Atualiza parcialmente um cupom. Requer autenticação de administrador.",
        request=CouponSerializer,
        responses={
            200: OpenApiResponse(
                response=CouponSerializer,
                description="Cupom atualizado com sucesso",
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
            ),
            404: OpenApiResponse(
                description="Cupom não encontrado",
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        operation_id="admin_coupons_delete",
        tags=["orders", "admin"],
        summary="Deletar cupom (Admin)",
        description="Deleta um cupom. Requer autenticação de administrador.",
        responses={
            204: OpenApiResponse(
                description="Cupom deletado com sucesso",
            ),
            404: OpenApiResponse(
                description="Cupom não encontrado",
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
