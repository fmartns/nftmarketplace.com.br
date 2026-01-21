from rest_framework import serializers
from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    """
    Serializer para banners - usado na API pública
    """

    class Meta:
        model = Banner
        fields = [
            "id",
            "title",
            "image_url",
            "image_mobile",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BannerAdminSerializer(serializers.ModelSerializer):
    """
    Serializer para admin - inclui campo is_active
    """

    class Meta:
        model = Banner
        fields = [
            "id",
            "title",
            "image_url",
            "image_mobile",
            "is_active",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
