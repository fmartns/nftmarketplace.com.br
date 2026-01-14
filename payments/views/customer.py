"""
Views para clientes AbacatePay
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..models import AbacatePayCustomer
from ..serializers import CustomerSerializer
from ..services import AbacatePayService
from ..docs.customer import (
    customer_create_schema,
    customer_list_schema,
)


class CustomerCreateView(APIView):
    """
    View para criar um cliente na AbacatePay
    """

    permission_classes = [IsAuthenticated]

    @customer_create_schema
    def post(self, request):
        """Cria um cliente na AbacatePay para o usuário autenticado"""
        # Verifica se já existe cliente
        if hasattr(request.user, "abacatepay_customer"):
            return Response(
                {
                    "message": "Cliente já existe",
                    "customer": CustomerSerializer(
                        request.user.abacatepay_customer
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        user_name = (
            f"{request.user.first_name or ''} {request.user.last_name or ''}".strip()
        )
        if not user_name:
            user_name = request.user.username or request.user.email
            if not user_name:
                return Response(
                    {
                        "error": "Nome do usuário é obrigatório. Complete seu perfil com nome completo."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        customer_response = AbacatePayService.create_customer(
            user_id=str(request.user.id),
            email=request.user.email,
            name=user_name,
            cellphone=request.user.telefone,
            tax_id=request.user.cpf,
            metadata={
                "username": request.user.username or "",
                "first_name": request.user.first_name or "",
                "last_name": request.user.last_name or "",
            },
        )

        if customer_response.get("error"):
            return Response(
                {
                    "error": "Erro ao criar cliente na AbacatePay",
                    "details": customer_response["error"],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        customer_data = customer_response["data"]

        customer = AbacatePayCustomer.objects.create(
            user=request.user,
            external_id=customer_data["id"],
            metadata=customer_data.get("metadata", {}),
        )

        return Response(
            CustomerSerializer(customer).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerListView(APIView):
    """
    View para listar clientes (apenas para admin)
    """

    permission_classes = [IsAuthenticated]

    @customer_list_schema
    def get(self, request):
        """Lista clientes (apenas admin pode ver todos)"""
        if not request.user.is_staff:
            if hasattr(request.user, "abacatepay_customer"):
                serializer = CustomerSerializer(request.user.abacatepay_customer)
                return Response([serializer.data])
            return Response([])

        customers = AbacatePayCustomer.objects.select_related("user").order_by(
            "-created_at"
        )
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)
