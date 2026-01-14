"""
Views para autenticação MetaMask
"""

import secrets
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from ..serializers import (
    MetaMaskAuthSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from ..utils import verify_metamask_signature, get_tokens_for_user
from ..docs.metamask import (
    metamask_auth_schema,
    metamask_register_schema,
    generate_auth_message_schema,
)

User = get_user_model()


class MetaMaskAuthView(APIView):
    permission_classes = [AllowAny]

    @metamask_auth_schema
    def post(self, request):
        serializer = MetaMaskAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        assert validated_data is not None
        wallet_address = validated_data["wallet_address"].lower()
        signature = validated_data["signature"]
        message = validated_data["message"]

        if not verify_metamask_signature(wallet_address, message, signature):
            return Response(
                {"error": "Assinatura inválida"}, status=status.HTTP_401_UNAUTHORIZED
            )

        user, created = User.objects.get_or_create(
            wallet_address=wallet_address,
            defaults={"username": f"user_{wallet_address[-8:]}", "is_active": True},
        )

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "access_token": tokens["access"],
                "refresh_token": tokens["refresh"],
                "user": UserSerializer(user).data,
                "is_new_user": created,
            }
        )


class MetaMaskRegisterView(APIView):
    permission_classes = [AllowAny]

    @metamask_register_schema
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_data = serializer.validated_data
        assert user_data is not None
        wallet_address = user_data["wallet_address"].lower()
        signature = user_data["signature"]
        message = user_data["message"]

        if not verify_metamask_signature(wallet_address, message, signature):
            return Response(
                {"error": "Assinatura inválida"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Remove campos de assinatura dos dados do usuário
        clean_user_data = user_data.copy()
        clean_user_data.pop("signature", None)
        clean_user_data.pop("message", None)

        user = User.objects.create(**clean_user_data)
        tokens = get_tokens_for_user(user)

        return Response(
            {
                "access_token": tokens["access"],
                "refresh_token": tokens["refresh"],
                "user": UserSerializer(user).data,
                "is_new_user": True,
            },
            status=status.HTTP_201_CREATED,
        )


class GenerateAuthMessageView(APIView):
    permission_classes = [AllowAny]

    @generate_auth_message_schema
    def get(self, request):
        wallet_address = request.query_params.get("wallet_address")

        if not wallet_address:
            return Response(
                {"error": "Endereço da carteira é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nonce = secrets.token_hex(16)
        timestamp = timezone.now().isoformat()

        message = f"""Bem-vindo ao NFT Portal!

Esta solicitação não custará nada.

Endereço da carteira: {wallet_address}
Nonce: {nonce}
Timestamp: {timestamp}

Assine esta mensagem para autenticar-se no NFT Portal."""

        return Response({"message": message, "nonce": nonce, "timestamp": timestamp})
