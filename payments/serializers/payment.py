"""
Serializers para pagamentos AbacatePay
"""

from rest_framework import serializers
from ..models import AbacatePayPayment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer para pagamento AbacatePay"""

    order_id = serializers.CharField(source="order.order_id", read_only=True)
    billing_id = serializers.CharField(
        source="billing.billing_id",
        read_only=True,
    )

    class Meta:
        model = AbacatePayPayment
        fields = [
            "id",
            "billing",
            "billing_id",
            "order",
            "order_id",
            "payment_url",
            "amount",
            "status",
            "payment_method",
            "created_at",
            "updated_at",
            "paid_at",
        ]
        read_only_fields = [
            "id",
            "billing_id",
            "payment_url",
            "status",
            "payment_method",
            "created_at",
            "updated_at",
            "paid_at",
        ]
