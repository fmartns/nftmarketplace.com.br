"""
Serializers para pedidos
"""

from rest_framework import serializers
from decimal import Decimal
from typing import Optional
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field

from ..models import Order, OrderItem, Coupon
from .coupon import CouponSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para item do pedido"""

    item_type = serializers.SerializerMethodField()
    item_name = serializers.SerializerMethodField()
    item_image_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "content_type",
            "object_id",
            "item_type",
            "item_name",
            "item_image_url",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "content_type",
            "object_id",
            "unit_price",
            "total_price",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_item_type(self, obj) -> Optional[str]:
        """Retorna o tipo do item ('legacy' ou 'nft')"""
        if obj.content_type.model == "item":
            return "legacy"
        elif obj.content_type.model == "nftitem":
            return "nft"
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_item_name(self, obj) -> Optional[str]:
        """Retorna o nome do item"""
        if obj.item:
            if hasattr(obj.item, "name"):
                return obj.item.name
            elif hasattr(obj.item, "name_pt_br") and obj.item.name_pt_br:
                return obj.item.name_pt_br
        return None

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_item_image_url(self, obj) -> Optional[str]:
        """Retorna a URL da imagem do item"""
        if obj.item and hasattr(obj.item, "image_url"):
            return obj.item.image_url
        return None


class OrderSerializer(serializers.ModelSerializer):
    """Serializer para pedido"""

    items = OrderItemSerializer(many=True, read_only=True)
    coupon_detail = CouponSerializer(source="coupon", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "user",
            "user_email",
            "user_username",
            "status",
            "subtotal",
            "discount_amount",
            "total",
            "coupon",
            "coupon_detail",
            "paid_at",
            "delivered",
            "delivered_at",
            "delivered_by",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "order_id",
            "subtotal",
            "discount_amount",
            "total",
            "paid_at",
            "delivered",
            "delivered_at",
            "delivered_by",
            "created_at",
            "updated_at",
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer para criar item do pedido"""

    item_type = serializers.ChoiceField(
        choices=[("legacy", "Legacy Item"), ("nft", "NFT Item")],
        help_text="Tipo do item: 'legacy' ou 'nft'",
    )
    item_id = serializers.IntegerField(
        help_text="ID do item (legacy.Item.id ou nft.NFTItem.id)",
    )
    quantity = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Quantidade do item",
    )

    def validate(self, attrs):
        """Valida se o item existe e obtém o preço"""
        item_type = attrs.get("item_type")
        item_id = attrs.get("item_id")
        quantity = attrs.get("quantity") or 1

        if item_type == "legacy":
            try:
                content_type = ContentType.objects.get(app_label="legacy", model="item")
                from legacy.models import Item

                item = Item.objects.get(id=item_id)
                unit_price = item.last_price
                if quantity > 1 and not getattr(item, "can_buy_multiple", False):
                    raise serializers.ValidationError(
                        "Este item legacy não permite compra em quantidade."
                    )
                if (
                    item.available_offers
                    and item.available_offers > 0
                    and quantity > item.available_offers
                ):
                    raise serializers.ValidationError(
                        f"Quantidade indisponível. Máximo: {item.available_offers}."
                    )
            except ContentType.DoesNotExist:
                raise serializers.ValidationError(
                    "Tipo de item 'legacy' não encontrado."
                )
            except Item.DoesNotExist:
                raise serializers.ValidationError(
                    f"Item legacy com ID {item_id} não encontrado."
                )

        elif item_type == "nft":
            try:
                content_type = ContentType.objects.get(app_label="nft", model="nftitem")
                from nft.models import NFTItem

                item = NFTItem.objects.get(id=item_id)
                unit_price = item.last_price_brl or Decimal("0.00")
                if unit_price == Decimal("0.00"):
                    raise serializers.ValidationError(
                        f"Item NFT com ID {item_id} não possui preço configurado."
                    )
            except ContentType.DoesNotExist:
                raise serializers.ValidationError("Tipo de item 'nft' não encontrado.")
            except NFTItem.DoesNotExist:
                raise serializers.ValidationError(
                    f"Item NFT com ID {item_id} não encontrado."
                )

        else:
            raise serializers.ValidationError("Tipo de item inválido.")

        attrs["content_type"] = content_type
        attrs["object_id"] = item_id
        attrs["unit_price"] = unit_price
        attrs["item"] = item

        return attrs


class OrderCreateSerializer(serializers.Serializer):
    """Serializer para criar pedido"""

    items = OrderItemCreateSerializer(
        many=True,
        min_length=1,
        help_text="Lista de itens do pedido",
    )
    coupon_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Código do cupom (opcional)",
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Observações do pedido",
    )

    def validate_coupon_code(self, value):
        """Valida o código do cupom se fornecido"""
        if not value:
            return value

        try:
            coupon = Coupon.objects.get(code=value.upper())
            if not coupon.is_valid():
                raise serializers.ValidationError("Cupom não é válido ou expirou.")
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Cupom não encontrado.")

        return value.upper()

    def validate_items(self, value):
        """Valida que há pelo menos um item"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Pedido deve ter pelo menos um item.")
        return value
