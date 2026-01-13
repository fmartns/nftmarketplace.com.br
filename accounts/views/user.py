"""
Views para operações de usuário
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..serializers import UserSerializer
from ..docs.user import (
    user_profile_get_schema,
    user_profile_update_schema,
    user_profile_partial_update_schema,
)


class UserProfileView(APIView):
    """
    View para gerenciar o perfil do usuário autenticado.
    GET: Retorna dados do perfil
    PUT/PATCH: Atualiza dados do perfil
    """
    permission_classes = [IsAuthenticated]

    @user_profile_get_schema
    def get(self, request):
        """Retorna dados do perfil do usuário autenticado"""
        return Response(UserSerializer(request.user).data)

    @user_profile_update_schema
    def put(self, request):
        """Atualiza dados do perfil do usuário (substituição completa)"""
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @user_profile_partial_update_schema
    def patch(self, request):
        """Atualiza dados do perfil do usuário (atualização parcial)"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
