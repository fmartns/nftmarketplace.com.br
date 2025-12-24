"""
Serializers para autenticação
"""

from rest_framework import serializers
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .user import UserSerializer

User = get_user_model()


class MetaMaskAuthSerializer(serializers.Serializer):
    """Serializer para autenticação via MetaMask"""

    wallet_address = serializers.CharField(
        max_length=42,
        validators=[
            RegexValidator(
                regex=r"^0x[a-fA-F0-9]{40}$",
                message="Endereço da carteira deve ser um endereço Ethereum válido",
            )
        ],
    )

    signature = serializers.CharField(
        max_length=132, help_text="Assinatura da mensagem com a carteira"
    )

    message = serializers.CharField(
        max_length=500, help_text="Mensagem que foi assinada"
    )


class AuthResponseSerializer(serializers.Serializer):
    """Serializer para resposta de autenticação"""

    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer()
    is_new_user = serializers.BooleanField(default=False)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado que permite autenticação via username/password ou wallet_address"""
    
    wallet_address = serializers.CharField(
        max_length=42,
        required=False,
        allow_blank=True,
        validators=[
            RegexValidator(
                regex=r"^0x[a-fA-F0-9]{40}$",
                message="Endereço da carteira deve ser um endereço Ethereum válido",
            )
        ],
    )
    
    signature = serializers.CharField(
        max_length=132,
        required=False,
        allow_blank=True,
        help_text="Assinatura da mensagem com a carteira (obrigatório se wallet_address for fornecido)"
    )
    
    message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Mensagem que foi assinada (obrigatório se wallet_address for fornecido)"
    )

    def validate(self, attrs):
        wallet_address = attrs.get("wallet_address", "").strip().lower()
        signature = attrs.get("signature", "").strip()
        message = attrs.get("message", "").strip()
        username = attrs.get("username", "").strip()
        password = attrs.get("password", "")

        # Se wallet_address foi fornecido, usar autenticação MetaMask
        if wallet_address:
            if not signature or not message:
                raise serializers.ValidationError(
                    "signature e message são obrigatórios quando wallet_address é fornecido"
                )
            
            from ..utils import verify_metamask_signature
            
            if not verify_metamask_signature(wallet_address, message, signature):
                raise serializers.ValidationError("Assinatura inválida")
            
            # Criar usuário se não existir (similar ao MetaMaskAuthView)
            user, created = User.objects.get_or_create(
                wallet_address=wallet_address,
                defaults={"username": f"user_{wallet_address[-8:]}", "is_active": True},
            )
            
            if not user.is_active:
                raise serializers.ValidationError("Usuário inativo")
            
            refresh = self.get_token(user)
            data = {}
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
            return data
        
        # Caso contrário, usar autenticação padrão username/password
        if not username or not password:
            raise serializers.ValidationError(
                "username e password são obrigatórios quando wallet_address não é fornecido"
            )
        
        # Chama o método validate do pai para autenticação padrão
        return super().validate(attrs)
