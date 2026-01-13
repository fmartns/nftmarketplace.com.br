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
        Valida o formato do nick do Habbo.
        Não bloqueia se o nick já estiver vinculado a outro usuário - 
        a view irá desvincular automaticamente da conta antiga.
        """
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
