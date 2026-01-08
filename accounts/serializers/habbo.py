"""
Serializers para validação do Habbo
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import HabboValidationTask

User = get_user_model()


class HabboValidationSerializer(serializers.Serializer):
    """Serializer para iniciar validação do nick do Habbo"""

    nick_habbo = serializers.CharField(
        max_length=50, help_text="Nick do usuário no Habbo"
    )

    def validate_nick_habbo(self, value):
        """
        Valida se o nick não está em uso por outro usuário.
        Um nick do Habbo só pode estar associado a um usuário por vez.
        """
        user = self.context["request"].user
        existing_user = (
            User.objects.filter(nick_habbo=value).exclude(id=user.id).first()
        )
        if existing_user:
            raise serializers.ValidationError(
                "Este nick do Habbo já está associado a outro usuário. Um nick só pode estar vinculado a um usuário por vez."
            )
        return value


class HabboValidationStatusSerializer(serializers.ModelSerializer):
    """Serializer para status da validação do Habbo"""

    class Meta:
        model = HabboValidationTask
        fields = [
            "id",
            "nick_habbo",
            "palavra_validacao",
            "status",
            "resultado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
