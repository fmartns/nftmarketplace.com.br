"""
Serializers para cobranças AbacatePay
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import AbacatePayBilling, AbacatePayCustomer


class BillingCreateSerializer(serializers.Serializer):
    """Serializer para criar uma nova cobrança"""
    
    order_id = serializers.CharField(
        help_text="ID do pedido (ex: #KFNSFG)",
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Descrição da cobrança",
    )
    
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Metadados adicionais",
    )


class BillingSerializer(serializers.ModelSerializer):
    """Serializer para cobrança AbacatePay"""
    
    order_id = serializers.CharField(source="order.order_id", read_only=True)
    customer_external_id = serializers.CharField(
        source="customer.external_id",
        read_only=True,
    )
    
    class Meta:
        model = AbacatePayBilling
        fields = [
            "id",
            "billing_id",
            "order",
            "order_id",
            "customer",
            "customer_external_id",
            "payment_url",
            "amount",
            "status",
            "methods",
            "frequency",
            "dev_mode",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "billing_id",
            "payment_url",
            "status",
            "methods",
            "frequency",
            "dev_mode",
            "created_at",
            "updated_at",
        ]


class BillingStatusSerializer(serializers.Serializer):
    """Serializer para status de cobrança"""
    
    billing_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_url = serializers.URLField(required=False, allow_null=True)
    methods = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
