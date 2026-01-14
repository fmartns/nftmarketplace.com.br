"""
Serializers para clientes AbacatePay
"""

from rest_framework import serializers
from ..models import AbacatePayCustomer


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer para cliente AbacatePay"""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AbacatePayCustomer
        fields = [
            "id",
            "external_id",
            "user",
            "user_email",
            "user_username",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "external_id", "created_at", "updated_at"]
