from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .models import Item
from .utils import convert_item_price


class LegacyItemDetailsSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    last_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    available_offers = serializers.IntegerField(required=False)

    class Meta:
        model = Item
        fields = ["id", "name", "description", "slug", "last_price", "average_price", "available_offers", "image_url", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        """Valida se o slug foi fornecido"""
        if not value:
            raise serializers.ValidationError(_("Slug parameter is required"))
        return value

    def to_representation(self, instance):
        """Retorna os preços já convertidos (convertidos antes de salvar no banco)"""
        representation = super().to_representation(instance)
        
        # Os preços já estão convertidos no banco, usar Decimal para garantir 2 casas decimais
        if representation.get("last_price") is not None:
            representation["last_price"] = float(Decimal(str(instance.last_price)).quantize(Decimal('0.01')))
        
        if representation.get("average_price") is not None:
            representation["average_price"] = float(Decimal(str(instance.average_price)).quantize(Decimal('0.01')))
        
        return representation

class LegacyItemCreateSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    available_offers = serializers.IntegerField(required=False)
    last_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Item
        fields = ["id", "name", "description", "slug", "last_price", "average_price", "available_offers", "image_url", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        """Valida se o slug foi fornecido"""
        if not value:
            raise serializers.ValidationError(_("Slug parameter is required"))
        return value

    def to_representation(self, instance):
        """Retorna os preços já convertidos (convertidos antes de salvar no banco)"""
        representation = super().to_representation(instance)
        
        # Os preços já estão convertidos no banco, usar Decimal para garantir 2 casas decimais
        if representation.get("last_price") is not None:
            representation["last_price"] = float(Decimal(str(instance.last_price)).quantize(Decimal('0.01')))
        
        if representation.get("average_price") is not None:
            representation["average_price"] = float(Decimal(str(instance.average_price)).quantize(Decimal('0.01')))
        
        return representation


class LegacyItemListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de itens (apenas campos essenciais)"""
    
    class Meta:
        model = Item
        fields = ["name", "image_url", "slug", "last_price", "average_price", "available_offers"]
    
    def to_representation(self, instance):
        """Retorna os preços formatados com 2 casas decimais"""
        representation = super().to_representation(instance)
        
        # Formatar preços com 2 casas decimais
        if representation.get("last_price") is not None:
            representation["last_price"] = float(Decimal(str(instance.last_price)).quantize(Decimal('0.01')))
        
        if representation.get("average_price") is not None:
            representation["average_price"] = float(Decimal(str(instance.average_price)).quantize(Decimal('0.01')))
        
        return representation