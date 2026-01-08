"""
Serializers para usuários
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer para dados do usuário"""

    perfil_completo = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "cpf",
            "telefone",
            "data_nascimento",
            "nick_habbo",
            "habbo_validado",
            "wallet_address",
            "perfil_completo",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "nick_habbo",
            "habbo_validado",
            "perfil_completo",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro completo do usuário"""

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
        max_length=132,
        write_only=True,
        help_text="Assinatura da mensagem com a carteira",
    )

    message = serializers.CharField(
        max_length=500, write_only=True, help_text="Mensagem que foi assinada"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "cpf",
            "telefone",
            "data_nascimento",
            "nick_habbo",
            "wallet_address",
            "signature",
            "message",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_wallet_address(self, value):
        """Valida se a carteira já não está em uso"""
        if User.objects.filter(wallet_address=value).exists():
            raise serializers.ValidationError(
                "Esta carteira já está associada a outro usuário."
            )
        return value.lower()  # Normaliza para lowercase

    def validate_username(self, value):
        """Valida se o username já não está em uso"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def validate_nick_habbo(self, value):
        """
        Valida se o nick do Habbo já não está em uso.
        Um nick do Habbo só pode estar associado a um usuário por vez.
        """
        if value and User.objects.filter(nick_habbo=value).exists():
            raise serializers.ValidationError(
                "Este nick do Habbo já está associado a outro usuário. Um nick só pode estar vinculado a um usuário por vez."
            )
        return value
