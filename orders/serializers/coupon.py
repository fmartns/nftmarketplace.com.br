"""
Serializers para cupons
"""
from rest_framework import serializers
from django.utils import timezone

from ..models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    """Serializer para cupom"""
    
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "description",
            "discount_type",
            "discount_value",
            "min_purchase_amount",
            "max_discount_amount",
            "max_uses",
            "uses_count",
            "is_active",
            "valid_from",
            "valid_until",
            "is_valid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uses_count",
            "is_valid",
            "created_at",
            "updated_at",
        ]
    
    def get_is_valid(self, obj):
        """Retorna se o cupom é válido no momento"""
        return obj.is_valid()


class CouponValidateSerializer(serializers.Serializer):
    """Serializer para validar um cupom"""
    
    code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    
    def validate_code(self, value):
        """Valida se o código do cupom existe"""
        try:
            coupon = Coupon.objects.get(code=value.upper())
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Cupom não encontrado.")
        
        if not coupon.is_valid():
            raise serializers.ValidationError("Cupom não é válido ou expirou.")
        
        return value
    
    def validate(self, attrs):
        """Valida se o cupom pode ser aplicado ao valor"""
        code = attrs.get("code")
        amount = attrs.get("amount")
        
        try:
            coupon = Coupon.objects.get(code=code.upper())
            
            if amount < coupon.min_purchase_amount:
                raise serializers.ValidationError(
                    f"Valor mínimo de compra para este cupom é R$ {coupon.min_purchase_amount}."
                )
            
            discount = coupon.calculate_discount(amount)
            attrs["discount"] = discount
            attrs["coupon"] = coupon
            
        except Coupon.DoesNotExist:
            pass
        
        return attrs





