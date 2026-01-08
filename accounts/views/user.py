"""
Views para operações de usuário
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from ..serializers import UserSerializer


class UserProfileView(APIView):
    """
    View para gerenciar o perfil do usuário autenticado.
    GET: Retorna dados do perfil
    PUT/PATCH: Atualiza dados do perfil
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="user_profile_get",
        tags=["accounts"],
        summary="Obter dados do perfil do usuário",
        description="Retorna os dados completos do perfil do usuário autenticado.",
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Dados do perfil retornados com sucesso",
            ),
        },
    )
    def get(self, request):
        """Retorna dados do perfil do usuário autenticado"""
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        operation_id="user_profile_update",
        tags=["accounts"],
        summary="Atualizar dados do perfil do usuário",
        description="Atualiza os dados do perfil do usuário autenticado. Campos opcionais podem ser omitidos.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Perfil atualizado com sucesso",
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
            ),
        },
    )
    def put(self, request):
        """Atualiza dados do perfil do usuário (substituição completa)"""
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="user_profile_partial_update",
        tags=["accounts"],
        summary="Atualizar parcialmente dados do perfil do usuário",
        description="Atualiza parcialmente os dados do perfil do usuário autenticado. Apenas os campos enviados serão atualizados.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Perfil atualizado com sucesso",
            ),
            400: OpenApiResponse(
                description="Dados inválidos",
            ),
        },
    )
    def patch(self, request):
        """Atualiza dados do perfil do usuário (atualização parcial)"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
