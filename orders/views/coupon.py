"""
Views para cupons
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import Coupon
from ..serializers import CouponSerializer, CouponValidateSerializer


class CouponValidateView(APIView):
    """
    View para validar um cupom
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="coupons_validate",
        tags=["orders"],
        summary="Validar cupom",
        description="""
        Valida um cupom e retorna o desconto que seria aplicado a um valor.
        
        **Retorna:**
        - Se o cupom é válido
        - Valor do desconto que seria aplicado
        - Informações do cupom
        """,
        request=CouponValidateSerializer,
        responses={
            200: OpenApiResponse(
                description="Cupom validado com sucesso",
                examples=[
                    {
                        "valid": True,
                        "discount": "10.00",
                        "code": "DESCONTO20",
                        "discount_type": "percentage",
                        "discount_value": "20.00",
                    },
                ],
            ),
            400: OpenApiResponse(
                description="Cupom inválido ou valor insuficiente",
            ),
        },
    )
    def post(self, request):
        """Valida um cupom"""
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        coupon = validated_data["coupon"]
        discount = validated_data["discount"]
        
        return Response(
            {
                "valid": True,
                "discount": str(discount),
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": str(coupon.discount_value),
                "min_purchase_amount": str(coupon.min_purchase_amount),
            },
            status=status.HTTP_200_OK,
        )


class CouponListView(generics.ListCreateAPIView):
    """
    View para listar e criar cupons (apenas admin)
    """
    permission_classes = [IsAdminUser]
    serializer_class = CouponSerializer
    queryset = Coupon.objects.all().order_by("-created_at")
    
    @extend_schema(
        operation_id="coupons_list",
        tags=["orders", "admin"],
        summary="Listar cupons (Admin)",
        description="Lista todos os cupons disponíveis. Requer autenticação de administrador.",
        responses={
            200: OpenApiResponse(
                response=CouponSerializer(many=True),
                description="Lista de cupons retornada com sucesso",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        operation_id="coupons_create",
        tags=["orders", "admin"],
        summary="Criar cupom (Admin)",
        description="Cria um novo cupom de desconto. Requer autenticação de administrador.",
        request=CouponSerializer,
        responses={
            201: OpenApiResponse(
                response=CouponSerializer,
                description="Cupom criado com sucesso",
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Cria um novo cupom"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Define created_by como o usuário autenticado
        coupon = serializer.save(created_by=request.user)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
