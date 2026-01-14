"""
Views customizadas para autenticação JWT
"""

from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.auth import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada que permite autenticação via username/password ou wallet_address
    """

    serializer_class = CustomTokenObtainPairSerializer
