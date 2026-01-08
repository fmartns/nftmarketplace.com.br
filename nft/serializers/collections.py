from rest_framework import serializers
from ..models import NftCollection


class NftCollectionSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(read_only=True)
    author = serializers.CharField(read_only=True)
    floor_price_eth = serializers.CharField(read_only=True)
    total_volume_eth = serializers.CharField(read_only=True)

    class Meta:
        model = NftCollection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "address",
            "profile_image",
            "cover_image",
            "creator",
            "creator_name",
            "author",
            "items_count",
            "owners_count",
            "floor_price",
            "floor_price_eth",
            "total_volume",
            "total_volume_eth",
            "metadata_api_url",
            "project_id",
            "project_owner_address",
            "website_url",
            "twitter_url",
            "instagram_url",
            "discord_url",
            "telegram_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "author",
            "floor_price_eth",
            "total_volume_eth",
        ]

    def validate(self, attrs):
        """Garante que URLs vazias sejam string vazia ao invés de None"""
        data = attrs
        url_fields = [
            "website_url",
            "twitter_url",
            "instagram_url",
            "discord_url",
            "telegram_url",
            "profile_image",
            "cover_image",
            "metadata_api_url",
        ]
        for field in url_fields:
            if field in data and data[field] is None:
                data[field] = ""
        return data
